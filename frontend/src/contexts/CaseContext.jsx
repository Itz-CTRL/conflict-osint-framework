// src/contexts/CaseContext.jsx
import { createContext, useContext, useState, useCallback } from 'react';
import { api } from '../utils/api';

const CaseContext = createContext(null);

export function CaseProvider({ children }) {
  // Case management
  const [investigations, setInvestigations] = useState([]);
  const [currentCase, setCurrentCase] = useState(null);
  const [loadingList, setLoadingList] = useState(false);
  
  // Phone history
  const [phoneHistory, setPhoneHistory] = useState([]);
  
  // UI state
  const [activeTab, setActiveTab] = useState('investigations'); // dashboard active tab
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Investigation filters
  const [investigationFilters, setInvestigationFilters] = useState({
    platforms: [],
    location: '',
    accountType: '', // 'personal', 'business', 'bot'
    verified: null // null, true, false
  });
  
  // Graph interaction
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphFilters, setGraphFilters] = useState({
    nodeTypes: ['profile', 'platform', 'email', 'phone', 'keyword', 'mention'],
    edgeTypes: ['MENTIONS', 'CONNECTED_TO', 'USES_EMAIL', 'USES_PHONE', 'POSTED_KEYWORD', 'REPORTED_AS', 'SIMILAR_USERNAME'],
    minConfidence: 0.0
  });
  
  // Scan progress tracking
  const [scanProgress, setScanProgress] = useState({
    active: false,
    scanType: 'light', // 'light' or 'deep'
    percentage: 0,
    phase: 'initializing',
    message: ''
  });

  /**
   * Refresh investigations list from API
   */
  const refreshInvestigations = useCallback(async () => {
    setLoadingList(true);
    try {
      const res = await api.listInvestigations();
      const list = res.data || [];
      setInvestigations(list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (err) {
      setError(err.message);
      setInvestigations([]);
    } finally {
      setLoadingList(false);
    }
  }, []);

  /**
   * Add phone lookup to history
   */
  const addPhoneLookup = useCallback((result) => {
    setPhoneHistory(prev => [{ ...result, _ts: Date.now() }, ...prev].slice(0, 50));
  }, []);

  /**
   * Start scan progress tracking
   */
  const startScan = useCallback((scanType = 'light') => {
    setScanProgress({
      active: true,
      scanType,
      percentage: 0,
      phase: 'initializing',
      message: `Starting ${scanType} scan...`
    });
  }, []);

  /**
   * Update scan progress
   */
  const updateProgress = useCallback((phase, percentage, message) => {
    setScanProgress(prev => ({
      ...prev,
      phase,
      percentage: Math.min(Math.max(percentage, 0), 100),
      message
    }));
  }, []);

  /**
   * Complete scan
   */
  const completeScan = useCallback(() => {
    setScanProgress({
      active: false,
      scanType: 'light',
      percentage: 100,
      phase: 'completed',
      message: 'Scan completed'
    });
  }, []);

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <CaseContext.Provider value={{
      // Cases
      investigations,
      setInvestigations,
      currentCase,
      setCurrentCase,
      
      // Loading & errors
      loadingList,
      loading,
      setLoading,
      error,
      setError,
      clearError,
      
      // API actions
      refreshInvestigations,
      
      // Phone history
      phoneHistory,
      addPhoneLookup,
      
      // UI state
      activeTab,
      setActiveTab,
      
      // Investigation filters
      investigationFilters,
      setInvestigationFilters,
      
      // Graph state
      selectedNode,
      setSelectedNode,
      graphFilters,
      setGraphFilters,
      
      // Scan progress
      scanProgress,
      startScan,
      updateProgress,
      completeScan
    }}>
      {children}
    </CaseContext.Provider>
  );
}

export function useCaseContext() {
  const ctx = useContext(CaseContext);
  if (!ctx) throw new Error('useCaseContext must be used within CaseProvider');
  return ctx;
}
