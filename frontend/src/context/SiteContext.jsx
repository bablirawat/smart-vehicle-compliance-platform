import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from './AuthContext';

const SiteContext = createContext(null);

export const SiteProvider = ({ children }) => {
  const { user } = useAuth();
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState(1);
  const [loading, setLoading] = useState(false);

  const fetchSites = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await api.get('/sites');
      setSites(response.data);
      if (user.site_id) {
        setSelectedSiteId(user.site_id);
      } else if (response.data.length > 0 && !selectedSiteId) {
        setSelectedSiteId(response.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load sites:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, [user]);

  const selectedSite = sites.find((s) => s.id === Number(selectedSiteId)) || sites[0];

  return (
    <SiteContext.Provider value={{ sites, selectedSiteId, setSelectedSiteId, selectedSite, fetchSites, loading }}>
      {children}
    </SiteContext.Provider>
  );
};

export const useSite = () => useContext(SiteContext);
