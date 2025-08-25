import React, { useContext } from 'react';
import { connect as dvaConnect } from 'dva';
import ReduxContext from './ReduxContext';

// Modern connect HOC that uses React Context API instead of legacy childContextTypes
export const connect = (mapStateToProps, mapDispatchToProps) => {
  return (Component) => {
    // Create a wrapper component that uses the modern context API
    const ConnectedComponent = React.memo((props) => {
      // Get the store from context
      const store = useContext(ReduxContext);
      
      // Create a component that uses the dva connect but with our store
      const DvaConnected = React.useMemo(() => {
        // Use the original dva connect with the component
        return dvaConnect(mapStateToProps, mapDispatchToProps)(Component);
      }, []);
      
      // Render the connected component with the store and other props
      return <DvaConnected {...props} store={store} />;
    });
    
    // Set display name for debugging
    ConnectedComponent.displayName = `ModernConnect(${Component.displayName || Component.name || 'Component'})`;
    
    return ConnectedComponent;
  };
};

// Modern Provider component that uses React.createContext
export const Provider = ({ store, children }) => (
  <ReduxContext.Provider value={store}>
    {children}
  </ReduxContext.Provider>
); 