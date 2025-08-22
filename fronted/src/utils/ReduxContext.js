import React from 'react';

// Create a context for the Redux store
const ReduxContext = React.createContext(null);

// Create a custom hook for accessing the Redux store
export const useRedux = () => {
  const context = React.useContext(ReduxContext);
  if (context === null) {
    throw new Error('useRedux must be used within a ReduxProvider');
  }
  return context;
};

export default ReduxContext; 