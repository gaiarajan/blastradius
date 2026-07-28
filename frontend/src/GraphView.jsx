import { useState, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";
import "./index.css";

const API_BASE = "http://localhost:8000";

function getImpactColor(score) {
  if (score === undefined) return "#999999"; 
  const r = Math.round(69 + (230 - 69) * score);
  const g = Math.round(123 + (57 - 123) * score);
  const b = Math.round(157 + (70 - 157) * score);
  return `rgb(${r}, ${g}, ${b})`;
}

export default function GraphView() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [scores, setScores] = useState({}); 
  const [pulseTick, setPulseTick] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE}/graph`)
      .then((res) => {
        if (!res.ok) throw new Error(`back-end failed with ${res.status}`);
        return res.json();
      })
      .then((data) => {
        const nodes = (data.nodes || []).map((name) => ({ id: name }));
        const links = (data.edges || []).map((edge) => ({
          source: edge.source,
          target: edge.target,
          edge_type: edge.edge_type,
          impactWeight: edge.impactWeight ? Number(edge.impactWeight) : undefined,
        }));
        setGraphData({ nodes, links });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // rerender every 100ms so pulse animation keeps moving 
  useEffect(() => {
    if (!selectedNode) return;
    const interval = setInterval(() => setPulseTick((t) => t + 1), 100);
    return () => clearInterval(interval);
  }, [selectedNode]);

  function handleNodeClick(node) {
    if (selectedNode === node.id) {
      setSelectedNode(null);
      setScores({});
      return;
    }

    fetch(`${API_BASE}/blast-radius/${node.id}`)
      .then((res) => res.json())
      .then((blastData) => {
        const affected = blastData.affected || [];

        // /simulate gives us { node, impact: { nodeId: score } }.
        fetch(`${API_BASE}/simulate/${node.id}`)
          .then((res) => (res.ok ? res.json() : {}))
          .catch(() => ({}))
          .then((simData) => {
            const impact = simData.impact || {};
            const newScores = { [node.id]: 1 };
            affected.forEach((id) => {
              newScores[id] = impact[id] !== undefined ? Number(impact[id]) : 0.5;
            });
            setSelectedNode(node.id);
            setScores(newScores);
          });
      })
      .catch((err) => console.error("sparql-motion fetch failed:", err));
  }

  function handleBackgroundClick() {
    setSelectedNode(null);
    setScores({});
  }

  if (loading) {
    return <div className="status">Loading graph...</div>;
  }

  if (error) {
    return <div className="status">Failed to load graph: {String(error)}</div>;
  }

  const affectedCount = Object.keys(scores).length > 0 ? Object.keys(scores).length - 1 : 0;

  const affectedIds = Object.keys(scores).filter((id) => id !== selectedNode);

  return (
    <div className="graph-page">
      {selectedNode && (
        <div className="info-bar">
          Selected: <strong>{selectedNode}</strong> — {affectedCount} package(s) affected
        </div>
      )}

      {affectedIds.length > 0 && (
        <div className="affected-list">
          <div className="affected-list-title">Affected packages</div>
          <ul>
            {affectedIds.map((id) => (
              <li key={id}>{id}</li>
            ))}
          </ul>
        </div>
      )}

      <ForceGraph2D
        graphData={graphData}
        nodeId="id"
        onNodeClick={handleNodeClick}
        onBackgroundClick={handleBackgroundClick}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px sans-serif`;

          const score = scores[node.id];
          const isSelected = node.id === selectedNode;
          const isAffected = score !== undefined;

          let radius = isSelected ? 9 : 7;
          if (isAffected && !isSelected) {
            radius += Math.sin(Date.now() / 900) * 1;
          }

          ctx.beginPath();
          ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
          ctx.fillStyle = isSelected ? "#e63946" : getImpactColor(score);
          ctx.fill();

          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillStyle = isAffected ? "#000" : "#555";
          ctx.fillText(node.id, node.x, node.y + radius + 3);
        }}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 14, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        backgroundColor="#fafafa"
        linkLabel={(link) => {
          const type = link.edge_type || "unknown";
          const impactWeight = link.impactWeight !== undefined ? link.impactWeight.toFixed(2) : "n/a";
          return `${type} (criticality: ${impactWeight})`;
        }}
        linkWidth={(link) => (link.impactWeight ? 1 + link.impactWeight * 3 : 1)}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.15}
      />
    </div>
  );
}
