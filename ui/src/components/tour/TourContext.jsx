import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const TOUR_STORAGE_KEY = 'srl4c_tour_completed';

const TourContext = createContext(null);

export const useTour = () => {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error('useTour must be used within a TourProvider');
  }
  return context;
};

export const TourProvider = ({ children }) => {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasCompletedTour, setHasCompletedTour] = useState(() => {
    return localStorage.getItem(TOUR_STORAGE_KEY) === 'true';
  });

  const startTour = useCallback(() => {
    setCurrentStep(0);
    setIsActive(true);
  }, []);

  const endTour = useCallback((markCompleted = true) => {
    setIsActive(false);
    setCurrentStep(0);
    if (markCompleted) {
      localStorage.setItem(TOUR_STORAGE_KEY, 'true');
      setHasCompletedTour(true);
    }
  }, []);

  const nextStep = useCallback(() => {
    setCurrentStep(prev => prev + 1);
  }, []);

  const prevStep = useCallback(() => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  }, []);

  const goToStep = useCallback((step) => {
    setCurrentStep(step);
  }, []);

  const resetTourHistory = useCallback(() => {
    localStorage.removeItem(TOUR_STORAGE_KEY);
    setHasCompletedTour(false);
  }, []);

  const value = {
    isActive,
    currentStep,
    hasCompletedTour,
    startTour,
    endTour,
    nextStep,
    prevStep,
    goToStep,
    resetTourHistory,
  };

  return (
    <TourContext.Provider value={value}>
      {children}
    </TourContext.Provider>
  );
};

export default TourProvider;
