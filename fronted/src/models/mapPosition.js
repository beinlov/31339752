export default {
  namespace: 'mapPosition',

  state: {
    isSwapped: false,
  },

  reducers: {
    toggleMapPosition(state) {
      return {
        ...state,
        isSwapped: !state.isSwapped,
      };
    },
  },
}; 