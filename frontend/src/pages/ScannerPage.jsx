// This file is now deprecated - functionality moved to Home.jsx
// Kept for backwards compatibility
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ScannerPage = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    navigate('/', { replace: true });
  }, [navigate]);
  
  return null;
};

export default ScannerPage;
