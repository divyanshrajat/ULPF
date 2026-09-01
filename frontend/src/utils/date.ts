/**
 * Utility functions for Indian Standard Time (IST, UTC+5:30) timestamp handling.
 * Guarantees that all timestamps across ULPF are accurately parsed and formatted in real-time IST.
 */

export function parseToDate(value: string | number | Date | null | undefined): Date | null {
  if (!value) return null;
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value;

  if (typeof value === 'number') {
    // Determine seconds vs milliseconds
    const d = new Date(value < 1e11 ? value * 1000 : value);
    return isNaN(d.getTime()) ? null : d;
  }

  let str = String(value).trim();
  if (!str) return null;

  // Handle SQLite naive format: 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM:SS'
  // If no timezone offset (+/-HH:MM or Z) is present, append Z to treat as UTC baseline
  if (!/(Z|[+-]\d{2}(:\d{2})?)$/i.test(str)) {
    if (str.includes(' ')) {
      str = str.replace(' ', 'T');
    }
    str = str + 'Z';
  }

  const d = new Date(str);
  return isNaN(d.getTime()) ? null : d;
}

export function formatIST(
  value: string | number | Date | null | undefined,
  mode: 'datetime' | 'time' | 'date' | 'compact' = 'datetime'
): string {
  const d = parseToDate(value);
  if (!d) return '—';

  const timeZone = 'Asia/Kolkata';

  if (mode === 'time') {
    return (
      d.toLocaleTimeString('en-IN', {
        timeZone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }) + ' IST'
    );
  }

  if (mode === 'date') {
    return d.toLocaleDateString('en-IN', {
      timeZone,
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  }

  if (mode === 'compact') {
    const timeStr = d.toLocaleTimeString('en-IN', {
      timeZone,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
    const dateStr = d.toLocaleDateString('en-IN', {
      timeZone,
      day: '2-digit',
      month: 'short',
    });
    return `${dateStr}, ${timeStr} IST`;
  }

  // default 'datetime'
  const timeStr = d.toLocaleTimeString('en-IN', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
  const dateStr = d.toLocaleDateString('en-IN', {
    timeZone,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
  return `${dateStr} ${timeStr} IST`;
}

export function getNowISTString(): string {
  return formatIST(new Date(), 'datetime');
}
