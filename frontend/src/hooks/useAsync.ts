import { useCallback, useEffect, useRef, useState } from 'react';
import { apiError } from '../services/api';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  setData: (value: T | null) => void;
}

/**
 * Runs an API request on mount (and when `deps` change) and exposes loading /
 * error state. We deliberately keep `data: null` until a real response arrives —
 * no placeholder values, so the UI can tell "empty" apart from "not loaded".
 */
export function useAsync<T>(
  factory: () => Promise<T>,
  deps: unknown[] = [],
  options: { skip?: boolean } = {}
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!options.skip);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);
  const factoryRef = useRef(factory);
  factoryRef.current = factory;

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await factoryRef.current();
      if (alive.current) setData(result);
    } catch (err) {
      if (alive.current) setError(apiError(err, 'Could not load data from the server.'));
    } finally {
      if (alive.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (options.skip) {
      setLoading(false);
      return;
    }
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, reload: run, setData };
}

/** Debounce a fast-changing value (used by the doctor search box). */
export function useDebounced<T>(value: T, delay = 320): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

/** Persisted light/dark theme, applied to <html data-theme>. */
export function useTheme(): [boolean, () => void] {
  const [dark, setDark] = useState(() => localStorage.getItem('ms_dark') === '1');
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    localStorage.setItem('ms_dark', dark ? '1' : '0');
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      'content', dark ? '#171112' : '#F5EDE6',
    );
  }, [dark]);
  return [dark, () => setDark((d) => !d)];
}

