module.exports = {
  options: {
    mains: {
      overview: 'overview',
      analysis: 'analysis'
    }
  },
  use: [
    '@neutrinojs/airbnb',
    [
      '@neutrinojs/react',
      {
        html: {
          title: 'profile-app'
        }
      }
    ],
    (neutrino) => neutrino.config.output.filename('[name].js'),
  ]
};
