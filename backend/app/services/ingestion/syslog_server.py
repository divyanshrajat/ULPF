import asyncio
import logging
from app.services.ingestion.gateway import process_ingestion
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class SyslogUDPProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # We need a db session
        db = SessionLocal()
        try:
            # We assume a default source_id for UDP syslog or map by port
            # For MVP, let's use a dummy source_id or we can require port-to-source mapping.
            source_id = "syslog-udp-source"
            peer = f"{addr[0]}:{addr[1]}"
            asyncio.create_task(process_ingestion(
                db=db,
                source_id=source_id,
                payload=data,
                transport="udp",
                peer=peer
            ))
        except Exception as e:
            logger.error(f"Error processing UDP syslog: {e}")
        finally:
            db.close()

async def handle_tcp_syslog(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    peername = writer.get_extra_info('peername')
    peer = f"{peername[0]}:{peername[1]}" if peername else "unknown"
    source_id = "syslog-tcp-source"
    db = SessionLocal()
    try:
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break
            # Syslog usually newline delimited
            await process_ingestion(
                db=db,
                source_id=source_id,
                payload=data.rstrip(b'\n\r'),
                transport="tcp",
                peer=peer
            )
    except Exception as e:
        logger.error(f"Error processing TCP syslog: {e}")
    finally:
        db.close()
        writer.close()

async def start_syslog_servers():
    logger.info("Starting Syslog UDP server on port 5140...")
    loop = asyncio.get_running_loop()
    udp_transport, _ = await loop.create_datagram_endpoint(
        lambda: SyslogUDPProtocol(),
        local_addr=('0.0.0.0', 5140)
    )
    
    logger.info("Starting Syslog TCP server on port 5140...")
    tcp_server = await asyncio.start_server(
        handle_tcp_syslog, '0.0.0.0', 5140
    )
    
    return udp_transport, tcp_server
