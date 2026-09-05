"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Float, OrbitControls, Stars, Text } from "@react-three/drei";
import * as THREE from "three";
import { useMemo, useRef, useState } from "react";
import type { RunArtifactsBundle } from "../lib/api/client";

export interface NodeData {
  id: string;
  label: string;
  color: string;
  position: [number, number, number];
  role: string;
  description: string;
  targetTab: string;
  geometryType: "octahedron" | "torus" | "icosahedron" | "dodecahedron" | "cylinder" | "papers" | "box" | "cone" | "evidence";
}

const NODES: NodeData[] = [
  {
    id: "problem",
    label: "PROBLEM",
    color: "#f87171",
    position: [-2.4, 1.3, 0.4],
    role: "Engineering Bottleneck",
    description: "Identifies core failure modes, scaling barriers, and algorithmic limits in existing literature.",
    targetTab: "Overview",
    geometryType: "octahedron",
  },
  {
    id: "objective",
    label: "OBJECTIVE",
    color: "#38bdf8",
    position: [-1.5, 2.2, -0.6],
    role: "Target Capabilities",
    description: "Verifiable technical milestones and theoretical bounds to be achieved by the proposed idea.",
    targetTab: "Overview",
    geometryType: "torus",
  },
  {
    id: "method",
    label: "METHOD",
    color: "#818cf8",
    position: [1.7, 1.9, 0.5],
    role: "Algorithmic Strategy",
    description: "Mathematical formulation, loss functions, attention structures, or state-space updates.",
    targetTab: "Similarity",
    geometryType: "icosahedron",
  },
  {
    id: "technology",
    label: "TECHNOLOGY",
    color: "#63e6ff",
    position: [2.5, 0.7, -0.3],
    role: "System Stack",
    description: "Underlying frameworks, compute runtimes, hardware targets, and library primitives.",
    targetTab: "Overview",
    geometryType: "dodecahedron",
  },
  {
    id: "dataset",
    label: "DATASET",
    color: "#fb923c",
    position: [2.2, -1.1, 0.6],
    role: "Empirical Benchmarks",
    description: "Standard evaluation corpora, benchmark suites, perturbation datasets, and split conventions.",
    targetTab: "Coverage",
    geometryType: "cylinder",
  },
  {
    id: "papers",
    label: "PAPERS",
    color: "#34d399",
    position: [0.9, -2.3, -0.4],
    role: "Academic Literature",
    description: "Peer-reviewed publications retrieved from arXiv, Semantic Scholar, and Crossref.",
    targetTab: "Sources",
    geometryType: "papers",
  },
  {
    id: "repos",
    label: "REPOS",
    color: "#a78bfa",
    position: [-1.3, -2.0, 0.5],
    role: "Open-Source Implementations",
    description: "Canonical GitHub repositories, codebases, benchmarks, and active community forks.",
    targetTab: "Sources",
    geometryType: "box",
  },
  {
    id: "claims",
    label: "CLAIMS",
    color: "#f472b6",
    position: [-2.5, -0.8, -0.5],
    role: "Testable Hypotheses",
    description: "Discrete, falsifiable claims extracted from retrieved literature to verify technical grounding.",
    targetTab: "Evidence",
    geometryType: "cone",
  },
  {
    id: "evidence",
    label: "EVIDENCE",
    color: "#22d3ee",
    position: [0.0, 0.0, 2.5],
    role: "Provenance Passages",
    description: "Strictly bounded text excerpts linked directly to source DOIs, arXiv IDs, and repository URLs.",
    targetTab: "Evidence",
    geometryType: "evidence",
  },
];

function IdeaCore({ activeNode, isSelected }: { activeNode: string | null; isSelected: boolean }) {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.y += delta * 0.22;
      outerRef.current.rotation.x += delta * 0.08;
    }
    if (innerRef.current) {
      innerRef.current.rotation.y -= delta * 0.38;
      innerRef.current.rotation.z += delta * 0.15;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.45;
    }
  });

  const coreColor = activeNode ? "#38bdf8" : "#63e6ff";

  return (
    <group>
      {/* Outer crystalline faceted shell */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1.35, 1]} />
        <meshStandardMaterial
          color="#64748b"
          emissive={coreColor}
          emissiveIntensity={isSelected ? 0.9 : 0.45}
          metalness={0.9}
          roughness={0.1}
          transparent
          opacity={0.7}
          wireframe
        />
      </mesh>

      {/* Inner glowing energy nucleus */}
      <mesh ref={innerRef}>
        <octahedronGeometry args={[0.82, 2]} />
        <meshStandardMaterial
          color={coreColor}
          emissive={coreColor}
          emissiveIntensity={isSelected ? 3.8 : 2.6}
          metalness={0.3}
          roughness={0.2}
          transparent
          opacity={0.88}
        />
      </mesh>

      {/* Horizontal equatorial energy ring */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.5, 0.018, 16, 64]} />
        <meshBasicMaterial color={coreColor} transparent opacity={0.6} />
      </mesh>

      {/* Central label */}
      <Text
        position={[0, -0.02, 0]}
        fontSize={0.15}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.01}
        outlineColor="#020617"
      >
        IDEA CORE
      </Text>
    </group>
  );
}

function NodeGeometry({ type, color, isActive, isSelected }: { type: NodeData["geometryType"]; color: string; isActive: boolean; isSelected: boolean }) {
  const intensity = isSelected ? 4.5 : isActive ? 3.5 : 1.8;

  const mat = (
    <meshStandardMaterial
      color={color}
      emissive={color}
      emissiveIntensity={intensity}
      metalness={0.6}
      roughness={0.2}
    />
  );

  switch (type) {
    case "octahedron":
      return (
        <group>
          <mesh>{mat}<octahedronGeometry args={[0.26, 0]} /></mesh>
          {(isActive || isSelected) && (
            <mesh>
              <octahedronGeometry args={[0.34, 0]} />
              <meshBasicMaterial color={color} wireframe transparent opacity={0.5} />
            </mesh>
          )}
        </group>
      );
    case "torus":
      return (
        <group>
          <mesh rotation={[Math.PI / 3, 0, 0]}>{mat}<torusGeometry args={[0.22, 0.05, 16, 32]} /></mesh>
          <mesh>{mat}<sphereGeometry args={[0.13, 16, 16]} /></mesh>
        </group>
      );
    case "icosahedron":
      return (
        <group>
          <mesh>{mat}<icosahedronGeometry args={[0.25, 0]} /></mesh>
          <mesh>
            <icosahedronGeometry args={[0.33, 0]} />
            <meshBasicMaterial color={color} wireframe transparent opacity={0.4} />
          </mesh>
        </group>
      );
    case "dodecahedron":
      return (
        <group>
          <mesh>{mat}<dodecahedronGeometry args={[0.24, 0]} /></mesh>
          {(isActive || isSelected) && (
            <mesh rotation={[Math.PI / 4, 0, 0]}>
              <ringGeometry args={[0.32, 0.38, 24]} />
              <meshBasicMaterial color={color} transparent opacity={0.6} side={THREE.DoubleSide} />
            </mesh>
          )}
        </group>
      );
    case "cylinder":
      return (
        <group>
          <mesh rotation={[0, 0, Math.PI / 4]}>{mat}<cylinderGeometry args={[0.18, 0.18, 0.28, 16]} /></mesh>
          <mesh rotation={[0, 0, -Math.PI / 4]}>
            <cylinderGeometry args={[0.22, 0.22, 0.04, 16]} />
            <meshBasicMaterial color={color} wireframe transparent opacity={0.6} />
          </mesh>
        </group>
      );
    case "papers":
      return (
        <group>
          <mesh>{mat}<sphereGeometry args={[0.14, 16, 16]} /></mesh>
          <mesh rotation={[Math.PI / 2.5, 0, 0]}>
            <torusGeometry args={[0.26, 0.03, 16, 32]} />
            <meshBasicMaterial color={color} transparent opacity={0.8} />
          </mesh>
          <mesh rotation={[-Math.PI / 2.5, 0, 0]}>
            <torusGeometry args={[0.22, 0.02, 16, 32]} />
            <meshBasicMaterial color={color} transparent opacity={0.5} />
          </mesh>
        </group>
      );
    case "box":
      return (
        <group>
          <mesh>{mat}<boxGeometry args={[0.28, 0.28, 0.28]} /></mesh>
          {(isActive || isSelected) && (
            <mesh>
              <boxGeometry args={[0.38, 0.38, 0.38]} />
              <meshBasicMaterial color={color} wireframe transparent opacity={0.6} />
            </mesh>
          )}
        </group>
      );
    case "cone":
      return (
        <group>
          <mesh rotation={[Math.PI, 0, 0]}>{mat}<coneGeometry args={[0.22, 0.4, 4]} /></mesh>
        </group>
      );
    case "evidence":
      return (
        <group>
          <mesh>{mat}<octahedronGeometry args={[0.28, 1]} /></mesh>
          <mesh rotation={[Math.PI / 4, Math.PI / 4, 0]}>
            <octahedronGeometry args={[0.36, 0]} />
            <meshBasicMaterial color={color} wireframe transparent opacity={0.7} />
          </mesh>
        </group>
      );
  }
}

function ConstellationNode({
  node,
  isActive,
  isSelected,
  onHover,
  onClick,
}: {
  node: NodeData;
  isActive: boolean;
  isSelected: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current && (isActive || isSelected)) {
      groupRef.current.rotation.y += delta * 1.8;
    }
  });

  const scale = isSelected ? 1.45 : isActive ? 1.25 : 1.0;

  return (
    <group position={node.position}>
      <Float speed={1.8} rotationIntensity={0.3} floatIntensity={0.25}>
        <group
          ref={groupRef}
          onPointerOver={(e) => {
            e.stopPropagation();
            onHover(node.id);
          }}
          onPointerOut={() => onHover(null)}
          onClick={(e) => {
            e.stopPropagation();
            onClick(node.id);
          }}
          scale={scale}
        >
          <NodeGeometry
            type={node.geometryType}
            color={node.color}
            isActive={isActive}
            isSelected={isSelected}
          />
        </group>

        {/* Outer pulse aura if selected or active */}
        {(isActive || isSelected) && (
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.38, 0.44, 32]} />
            <meshBasicMaterial color={node.color} transparent opacity={isSelected ? 0.85 : 0.5} side={THREE.DoubleSide} />
          </mesh>
        )}

        {/* Node label */}
        <Text
          position={[0, 0.46, 0]}
          fontSize={0.12}
          color={isSelected ? "#ffffff" : isActive ? "#e2e8f0" : "#94a3b8"}
          anchorX="center"
          outlineWidth={0.015}
          outlineColor="#020617"
        >
          {node.label}
        </Text>
      </Float>
    </group>
  );
}

const CENTER_POINT: [number, number, number] = [0, 0, 0];

function ConnectionLines({ activeNode, selectedNode }: { activeNode: string | null; selectedNode: string | null }) {
  const currentFocused = selectedNode || activeNode;

  const lines = useMemo(() => {
    return NODES.map((node) => {
      const isTarget = currentFocused === node.id;
      const points = [CENTER_POINT, node.position];
      const geometry = new THREE.BufferGeometry().setFromPoints(
        points.map((p) => new THREE.Vector3(...p))
      );
      return {
        geometry,
        color: isTarget ? node.color : "#334155",
        opacity: isTarget ? 0.9 : 0.2,
      };
    });
  }, [currentFocused]);

  return (
    <group>
      {lines.map((line, idx) => (
        <primitive
          key={idx}
          object={
            new THREE.Line(
              line.geometry,
              new THREE.LineBasicMaterial({
                color: line.color,
                transparent: true,
                opacity: line.opacity,
              })
            )
          }
        />
      ))}
    </group>
  );
}

interface LensSceneProps {
  bundle?: RunArtifactsBundle | null;
  onSelectTab?: (tabName: string) => void;
}

export default function LensScene({ bundle, onSelectTab }: LensSceneProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const activeNodeId = hoveredNode || selectedNode;
  const activeNodeData = NODES.find((n) => n.id === activeNodeId) ?? null;

  // Derive genuine stats from bundle if present
  const nodeStats = useMemo(() => {
    if (!activeNodeData) return null;
    const decomposition = bundle?.run?.decomposition;

    switch (activeNodeData.id) {
      case "papers": {
        const papersCount = bundle?.sources?.filter((s) => s.source_kind === "paper").length || 0;
        return {
          metricLabel: "Retrieved Papers",
          metricValue: bundle ? `${papersCount} verified papers` : "14 benchmark papers (demo)",
          detail: "Indexed across arXiv, Semantic Scholar, and Crossref with DOI backrefs.",
        };
      }
      case "repos": {
        const reposCount = bundle?.sources?.filter((s) => s.source_kind === "repository" || s.adapter_id === "github").length || 0;
        return {
          metricLabel: "Code Repositories",
          metricValue: bundle ? `${reposCount} open-source repos` : "5 canonical implementations (demo)",
          detail: "Grounded with GitHub stars, licensing, and commit activity provenance.",
        };
      }
      case "evidence": {
        const count = bundle?.evidence?.length || 0;
        return {
          metricLabel: "Evidence Chain",
          metricValue: bundle ? `${count} grounded passages` : "21 extracted passages (demo)",
          detail: "Strictly bounded text substrings mapped to testable hypotheses.",
        };
      }
      case "claims": {
        const count = decomposition?.claims?.length || 0;
        return {
          metricLabel: "Testable Hypotheses",
          metricValue: count > 0 ? `${count} structured claims` : "3 falsifiable hypotheses (demo)",
          detail: "Core technical mechanisms subjected to cross-corpus verification.",
        };
      }
      case "method": {
        const methods = decomposition?.methods || [];
        return {
          metricLabel: "Algorithmic Approaches",
          metricValue: methods.length > 0 ? methods.join(", ") : "State-space models & multi-hop verification",
          detail: "Multi-dimensional similarity evaluated against prior publications.",
        };
      }
      case "technology": {
        const techs = decomposition?.technologies || [];
        return {
          metricLabel: "Technology Stack",
          metricValue: techs.length > 0 ? techs.join(", ") : "PyTorch, Vector Index, Knowledge Graph",
          detail: "Framework and architecture compatibility mapped across repos.",
        };
      }
      case "dataset": {
        const datasets = decomposition?.datasets || [];
        return {
          metricLabel: "Evaluation Datasets",
          metricValue: datasets.length > 0 ? datasets.join(", ") : "Standard academic benchmark splits",
          detail: "Sufficiency tiering: coverage evaluated per empirical benchmark.",
        };
      }
      case "problem": {
        const prob = decomposition?.problem;
        return {
          metricLabel: "Target Problem",
          metricValue: prob ? (prob.length > 60 ? `${prob.slice(0, 58)}…` : prob) : "Scalable reasoning bottlenecks",
          detail: "Cataloged failure modes and constraints identified in literature.",
        };
      }
      case "objective": {
        const obj = decomposition?.objective;
        return {
          metricLabel: "Core Objective",
          metricValue: obj ? (obj.length > 60 ? `${obj.slice(0, 58)}…` : obj) : "Verifiable multi-hop execution",
          detail: "Technical success criteria evaluated for defensibility.",
        };
      }
      default:
        return null;
    }
  }, [activeNodeData, bundle]);

  const handleNodeClick = (nodeId: string) => {
    if (selectedNode === nodeId) {
      setSelectedNode(null);
    } else {
      setSelectedNode(nodeId);
    }
  };

  const handleJumpToTab = (targetTab: string) => {
    if (onSelectTab) {
      onSelectTab(targetTab);
    }
    document.getElementById("workspace")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="relative h-[580px] w-full rounded-3xl border border-white/10 bg-slate-950/60 shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Header bar */}
      <div className="pointer-events-none absolute left-5 top-5 z-20 flex items-center gap-2 text-[10px] tracking-[.25em] text-cyan-400 font-mono">
        <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
        <span>3D RESEARCH GRAPH · 9 EVIDENCE NODES</span>
      </div>
      <div className="pointer-events-none absolute right-5 top-5 z-20 text-[10px] text-slate-500 font-mono">
        DRAG TO ROTATE · CLICK NODE TO INSPECT
      </div>

      {/* WebGL Canvas */}
      <Canvas camera={{ position: [0, 0, 7.8], fov: 46 }}>
        <color attach="background" args={["#020617"]} />
        <ambientLight intensity={0.45} />
        <pointLight position={[5, 5, 5]} intensity={35} color="#63e6ff" />
        <pointLight position={[-5, -4, 4]} intensity={25} color="#f472b6" />
        <pointLight position={[0, -5, -3]} intensity={20} color="#a78bfa" />
        <Stars radius={45} depth={15} count={1400} factor={1.4} saturation={0} />

        <IdeaCore activeNode={activeNodeId} isSelected={selectedNode !== null} />
        <ConnectionLines activeNode={hoveredNode} selectedNode={selectedNode} />

        {NODES.map((node) => (
          <ConstellationNode
            key={node.id}
            node={node}
            isActive={hoveredNode === node.id}
            isSelected={selectedNode === node.id}
            onHover={setHoveredNode}
            onClick={handleNodeClick}
          />
        ))}

        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={activeNodeId ? 0.12 : 0.4}
          maxPolarAngle={Math.PI / 1.7}
          minPolarAngle={Math.PI / 2.8}
        />
      </Canvas>

      {/* Screen-Space Non-Clipping Interactive HUD Overlay */}
      {activeNodeData && (
        <div
          role="dialog"
          aria-label={`Node details for ${activeNodeData.label}`}
          className="pointer-events-auto absolute bottom-4 left-4 right-4 z-30 mx-auto max-w-lg rounded-2xl border border-cyan-500/30 bg-slate-950/95 p-4 shadow-2xl backdrop-blur-xl transition-all duration-200 animate-in fade-in slide-in-from-bottom-2"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <span
                className="h-3 w-3 rounded-full shadow-lg"
                style={{ backgroundColor: activeNodeData.color, boxShadow: `0 0 12px ${activeNodeData.color}` }}
              />
              <span className="text-xs font-bold tracking-wider text-white font-mono">
                {activeNodeData.label}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-400 font-medium">
                {activeNodeData.role}
              </span>
            </div>
            {selectedNode && (
              <button
                onClick={() => setSelectedNode(null)}
                aria-label="Close node inspector"
                className="text-xs text-slate-400 hover:text-white transition"
              >
                ✕
              </button>
            )}
          </div>

          <p className="mt-2 text-xs leading-5 text-slate-300">
            {activeNodeData.description}
          </p>

          {nodeStats && (
            <div className="mt-3 rounded-xl border border-white/5 bg-white/5 p-2.5 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-cyan-300 font-mono">
                  {nodeStats.metricLabel}
                </span>
                <span className="font-medium text-slate-200 truncate max-w-[240px]">
                  {nodeStats.metricValue}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                {nodeStats.detail}
              </p>
            </div>
          )}

          <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-2.5">
            <span className="text-[10px] text-slate-500 font-mono">
              {selectedNode === activeNodeData.id ? "NODE SELECTED" : "HOVER PREVIEW · CLICK TO LOCK"}
            </span>
            <button
              onClick={() => handleJumpToTab(activeNodeData.targetTab)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-400/40 bg-cyan-400/10 px-3 py-1 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-400/20 hover:text-white"
            >
              <span>Explore in {activeNodeData.targetTab}</span>
              <span>→</span>
            </button>
          </div>
        </div>
      )}

      {/* Footer descriptor when no node is active */}
      {!activeNodeData && (
        <div className="pointer-events-none absolute bottom-4 left-5 z-20 text-[11px] text-slate-500 font-mono">
          Hover or click any node in the constellation to inspect evidence grounding.
        </div>
      )}
    </div>
  );
}