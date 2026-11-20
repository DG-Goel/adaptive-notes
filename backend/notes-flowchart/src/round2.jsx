import React from 'react';
import { createRoot } from 'react-dom/client';
import DiagramRenderer from './diagram/DiagramRenderer.jsx';
import DataStructureRenderer from './diagram/DataStructureRenderer.jsx';
import SequenceRenderer from './diagram/SequenceRenderer.jsx';
import { TablePreview } from '../../notes/table-render-test/src/App.jsx';
import './index.css';

const renderers = {
  table: TablePreview,
  flowchart: DiagramRenderer,
  architecture: DiagramRenderer,
  data_structure: DataStructureRenderer,
  sequence: SequenceRenderer,
};

window.renderRound2 = (data, id) => {
  const Renderer = renderers[data.type];
  if (!Renderer) throw new Error('Unsupported representation');
  root.render(<main key={id} id="visual" data-render-id={id} style={{background: 'white', padding: 16, width: 1400}}>
    <Renderer diagram={data} data={data}/>
  </main>);
};
const root = createRoot(document.getElementById('root'));
