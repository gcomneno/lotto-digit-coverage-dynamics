import { mount } from 'svelte';
import 'giadaware-ui-components/studio/styles.css';
import './styles.css';
import App from './App.svelte';

const target = document.getElementById('app');

if (!target) {
  throw new Error('GUI mount target not found.');
}

mount(App, { target });
