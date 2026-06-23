module.exports = function (api) {
  const isTest = api.env('test');
  api.cache.using(() => isTest);

  return {
    presets: ['expo/internal/babel-preset'],
    plugins: isTest ? [] : ['react-native-reanimated/plugin'],
  };
};
