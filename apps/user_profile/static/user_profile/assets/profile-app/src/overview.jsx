import { render } from 'react-dom';
import Overview from './OverviewContent';

const root = document.getElementById('root');
const load = () => render(
  (
    <Overview />
  ), root,
);

// This is needed for Hot Module Replacement
if (module.hot) {
  module.hot.accept('./Overview', load);
}

load();
