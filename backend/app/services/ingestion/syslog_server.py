import asyncio
import logging
from app.services.ingestion.gateway import process_ingestion
from app.core.database import SessionLocal
from app.models.domain import Source

logger = logging.getLogger(__name__)

def resolve_source(db, peer_ip: str) -> str:
    source = db.query(Source).filter(Source.namespace == peer_ip).first()
    if source:
        return source.source_id
    logger.warning(f"Unknown syslog source IP: {peer_ip}")
    return "unknown-syslog-source"


class SyslogUDPProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # We need a db session
        db = SessionLocal()
        try:
            peer_ip = addr[0]
            peer = f"{addr[0]}:{addr[1]}"
            source_id = resolve_source(db, peer_ip)
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
    peer_ip = peername[0] if peername else "unknown"
    peer = f"{peername[0]}:{peername[1]}" if peername else "unknown"
    db = SessionLocal()
    source_id = resolve_source(db, peer_ip)
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
