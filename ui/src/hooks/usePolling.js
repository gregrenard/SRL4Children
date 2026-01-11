import { useState, useEffect, useCallback } from 'react';

export const usePolling = (fetchFn, interval = 2000, shouldPoll = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    refresh();
    if (shouldPoll) {
      const id = setInterval(refresh, interval);
      return () => clearInterval(id);
    }
  }, [refresh, interval, shouldPoll]);

  return { data, loading, error, refresh };
};

export default usePolling;
