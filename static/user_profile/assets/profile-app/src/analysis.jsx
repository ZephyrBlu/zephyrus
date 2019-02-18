import { render } from 'react-dom';
import Analysis from './AnalysisContent';

const root = document.getElementById('root');
const load = () => render(
  (
    <Analysis />
  ), root,
);

// This is needed for Hot Module Replacement
if (module.hot) {
  module.hot.accept('./Overview', load);
}

load();
