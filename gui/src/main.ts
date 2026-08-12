import { mount } from 'svelte';
import 'giadaware-ui-components/styles.css';
import 'giadaware-ui-components/studio/styles.css';
import './styles.css';
import './theme-polish.css';
import App from './App.svelte';

document.documentElement.dataset.giuTheme = 'neutral';

const target = document.getElementById('app');

if (!target) {
  throw new Error('GUI mount target not found.');
}

mount(App, { target });
