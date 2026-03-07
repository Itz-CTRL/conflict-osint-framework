/**
 * Custom React hooks for OSINT Investigation Platform
 * useForm: Form state management
 * useApi: API calls with loading, error, and retry logic
 * useDebounce: Debounce values for search optimization
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Hook for managing form state with validation
 */
export function useForm(initialValues, onSubmit) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setValues(prev => ({
      ...prev,
      [name]: newValue,
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  }, [errors]);

  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true,
    }));
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await onSubmit(values);
    } catch (err) {
      console.error('Form submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [values, onSubmit]);

  const setFieldValue = useCallback((field, value) => {
    setValues(prev => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  const setFieldError = useCallback((field, error) => {
    setErrors(prev => ({
      ...prev,
      [field]: error,
    }));
  }, []);

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    setFieldError,
    setErrors,
    resetForm,
  };
}

/**
 * Hook for making API calls with loading and error handling
 */
export function useApi(apiFunction, options = {}) {
  const {
    immediate = true,
    onSuccess = null,
    onError = null,
    retryCount = 3,
    retryDelay = 1000,
  } = options;

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!!immediate);
  const [retries, setRetries] = useState(0);
  const abortControllerRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const result = await apiFunction(...args);
      setData(result);
      setRetries(0);

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err) {
      // Skip error if aborted
      if (err.name === 'AbortError') {
        return;
      }

      // Retry logic
      if (retries < retryCount) {
        setRetries(prev => prev + 1);

        retryTimeoutRef.current = setTimeout(() => {
          execute(...args);
        }, retryDelay * Math.pow(2, retries)); // Exponential backoff

        return;
      }

      setError(err);

      if (onError) {
        onError(err);
      }

      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, retries, retryCount, retryDelay, onSuccess, onError]);

  const refetch = useCallback(() => {
    setRetries(0);
    return execute();
  }, [execute]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    setData(null);
    setError(null);
    setLoading(false);
    setRetries(0);
  }, []);

  // Execute immediately if option is set
  useEffect(() => {
    if (immediate) {
      execute();
    }

    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  return {
    data,
    error,
    loading,
    retries,
    execute,
    refetch,
    reset,
  };
}

/**
 * Hook for debouncing values (useful for search inputs)
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for local storage management
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

/**
 * Hook for managing async state with loading, error, and data
 */
export function useAsync(asyncFunction, immediate = true) {
  const [status, setStatus] = useState('idle');
  const [value, setValue] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setStatus('pending');
    setValue(null);
    setError(null);

    try {
      const response = await asyncFunction(...args);
      setValue(response);
      setStatus('success');
      return response;
    } catch (err) {
      setError(err);
      setStatus('error');
      throw err;
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { execute, status, value, error };
}

/**
 * Hook for managing pagination state
 */
export function usePagination(initialPage = 1, itemsPerPage = 20) {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [itemsPerPage, setItemsPerPage] = useState(itemsPerPage);

  const goToPage = useCallback((page, maxPage) => {
    if (page >= 1 && page <= maxPage) {
      setCurrentPage(page);
    }
  }, []);

  const nextPage = useCallback((maxPage) => {
    setCurrentPage(prev => Math.min(prev + 1, maxPage));
  }, []);

  const prevPage = useCallback(() => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  }, []);

  const changeItemsPerPage = useCallback((newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to first page
  }, []);

  return {
    currentPage,
    itemsPerPage,
    goToPage,
    nextPage,
    prevPage,
    changeItemsPerPage,
    offset: (currentPage - 1) * itemsPerPage,
  };
}

/**
 * Hook for managing toggle/modal states
 */
export function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue(prev => !prev);
  }, []);

  const open = useCallback(() => {
    setValue(true);
  }, []);

  const close = useCallback(() => {
    setValue(false);
  }, []);

  const set = useCallback((newValue) => {
    setValue(newValue);
  }, []);

  return {
    value,
    toggle,
    open,
    close,
    set,
  };
}

/**
 * Hook for managing filtered lists
 */
export function useFilter(items, filterFunction) {
  const [filters, setFilters] = useState({});

  const filteredItems = items.filter(item => {
    for (const [key, filterValue] of Object.entries(filters)) {
      if (filterValue && !filterFunction(item, key, filterValue)) {
        return false;
      }
    }
    return true;
  });

  const addFilter = useCallback((key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const removeFilter = useCallback((key) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      delete newFilters[key];
      return newFilters;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  return {
    items: filteredItems,
    filters,
    addFilter,
    removeFilter,
    clearFilters,
  };
}

/**
 * Hook for managing undo/redo state
 */
export function useUndoRedo(initialValue) {
  const [state, setState] = useState(initialValue);
  const historyRef = useRef([initialValue]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const updateState = useCallback((newState) => {
    const newHistory = historyRef.current.slice(0, historyIndex + 1);
    newHistory.push(newState);
    historyRef.current = newHistory;
    setHistoryIndex(newHistory.length - 1);
    setState(newState);
  }, [historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setState(historyRef.current[newIndex]);
    }
  }, [historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < historyRef.current.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setState(historyRef.current[newIndex]);
    }
  }, [historyIndex]);

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < historyRef.current.length - 1;

  return {
    state,
    updateState,
    undo,
    redo,
    canUndo,
    canRedo,
  };
}

export default {
  useForm,
  useApi,
  useDebounce,
  useLocalStorage,
  useAsync,
  usePagination,
  useToggle,
  useFilter,
  useUndoRedo,
};
