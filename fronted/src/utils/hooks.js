import { useContext, useCallback } from 'react';
import ReduxContext from './ReduxContext';

// Hook for accessing the Redux state
export const useSelector = (selector) => {
  const store = useContext(ReduxContext);
  if (!store) {
    throw new Error('useSelector must be used within a Provider');
  }
  return selector(store.getState());
};

// Hook for dispatching actions
export const useDispatch = () => {
  const store = useContext(ReduxContext);
  if (!store) {
    throw new Error('useDispatch must be used within a Provider');
  }
  return useCallback((action) => store.dispatch(action), [store]);
};

// Combined hook for both state and dispatch
export const useRedux = (selector) => {
  const store = useContext(ReduxContext);
  if (!store) {
    throw new Error('useRedux must be used within a Provider');
  }
  
  const state = selector ? selector(store.getState()) : store.getState();
  const dispatch = useCallback((action) => store.dispatch(action), [store]);
  
  return { state, dispatch };
}; 