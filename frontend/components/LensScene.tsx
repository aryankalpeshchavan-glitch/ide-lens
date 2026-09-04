"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Float, OrbitControls, Stars, Text, Html } from "@react-three/drei";
import * as THREE from "three";
import { useMemo, useRef, useState } from "react";

interface NodeData {
  id: string;
  label: string;
  color: string;
  position: [number, number, number];
  description: string;
}

const NODES: NodeData[] = [
  { id: "problem", label: "PROBLEM", color: "#f87171", position: [-2.2, 1.2, 0.4], description: "Target engineering bottleneck and failure modes" },
  { id: "objective", label: "OBJECTIVE", color: "#38bdf8", position: [-1.4, 2.0, -0.6], description: "Verifiable technical goal and capabilities" },
  { id: "method", label: "METHOD", color: "#818cf8", position: [1.6, 1.8, 0.5], description: "Algorithmic formulation and mathematical strategy" },
  { id: "technology", label: "TECHNOLOGY", color: "#63e6ff", position: [2.3, 0.6, -0.3], description: "Underlying frameworks, models, and systems" },
  { id: "dataset", label: "DATASET", color: "#fb923c", position: [2.1, -1.0, 0.6], description: "Benchmark suites, training corpora, and splits" },
  { id: "papers", label: "PAPERS", color: "#34d399", position: [0.8, -2.1, -0.4], description: "Retrieved academic works via arXiv, S2, and Crossref" },
  { id: "repos", label: "REPOS", color: "#a78bfa", position: [-1.2, -1.9, 0.5], description: "Canonical GitHub repositories and implementations" },
  { id: "claims", label: "CLAIMS", color: "#f472b6", position: [-2.4, -0.7, -0.5], description: "Extracted testable technical hypotheses" },
  { id: "evidence", label: "EVIDENCE", color: "#22d3ee", position: [0.0, 0.0, 2.3], description: "Grounding excerpts with provenance backrefs" },
];

function IdeaCore({ activeNode }: { activeNode: string | null }) {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.y += delta * 0.18;
      outerRef.current.rotation.x += delta * 0.07;
    }
    if (innerRef.current) {
      innerRef.current.rotation.y -= delta * 0.35;
      innerRef.current.rotation.z += delta * 0.12;
    }
  });

  const coreColor = activeNode ? "#38bdf8" : "#63e6ff";

  return (
    <group>
      {/* Outer crystalline faceted shell */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1.45, 1]} />
        <meshStandardMaterial
          color="#94a3b8"
          emissive={coreColor}
          emissiveIntensity={0.35}
          metalness={0.85}
          roughness={0.12}
          transparent
          opacity={0.65}
          wireframe
        />
      </mesh>

      {/* Inner glowing energy nucleus */}
      <mesh ref={innerRef}>
        <octahedronGeometry args={[0.85, 2]} />
        <meshStandardMaterial
          color={coreColor}
          emissive={coreColor}
          emissiveIntensity={2.8}
          metalness={0.4}
          roughness={0.2}
          transparent
          opacity={0.82}
        />
      </mesh>

      {/* Central label */}
      <Text
        position={[0, -0.05, 0]}
        fontSize={0.16}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        IDEA CORE
      </Text>
    </group>
  );
}

function ConstellationNode({
  node,
  isActive,
  onHover,
  onClick,
}: {
  node: NodeData;
  isActive: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (meshRef.current && isActive) {
      meshRef.current.rotation.y += delta * 1.5;
    }
  });

  return (
    <group position={node.position}>
      <Float speed={1.8} rotationIntensity={0.4} floatIntensity={0.3}>
        <mesh
          ref={meshRef}
          onPointerOver={(e) => {
            e.stopPropagation();
            onHover(node.id);
          }}
          onPointerOut={() => onHover(null)}
          onClick={(e) => {
            e.stopPropagation();
            onClick(node.id);
          }}
          scale={isActive ? 1.45 : 1.0}
        >
          <sphereGeometry args={[0.22, 24, 24]} />
          <meshStandardMaterial
            color={node.color}
            emissive={node.color}
            emissiveIntensity={isActive ? 4.5 : 2.2}
            metalness={0.5}
            roughness={0.2}
          />
        </mesh>

        {/* Outer pulse ring if active */}
        {isActive && (
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.32, 0.38, 32]} />
            <meshBasicMaterial color={node.color} transparent opacity={0.7} side={THREE.DoubleSide} />
          </mesh>
        )}

        {/* Node label */}
        <Text
          position={[0, 0.42, 0]}
          fontSize={0.12}
          color={isActive ? "#ffffff" : "#cbd5e1"}
          anchorX="center"
          outlineWidth={0.015}
          outlineColor="#05070b"
        >
          {node.label}
        </Text>

        {/* Tooltip on active */}
        {isActive && (
          <Html distanceFactor={10} position={[0, -0.45, 0]} center>
            <div className="pointer-events-none whitespace-nowrap rounded-lg border border-cyan-400/30 bg-slate-950/90 px-3 py-1.5 text-[11px] text-cyan-200 shadow-xl backdrop-blur-md">
              <span className="font-semibold text-white">{node.label}:</span> {node.description}
            </div>
          </Html>
        )}
      </Float>
    </group>
  );
}

const CENTER_POINT: [number, number, number] = [0, 0, 0];

function ConnectionLines({ activeNode }: { activeNode: string | null }) {
  const lines = useMemo(() => {
    return NODES.map((node) => {
      const isTarget = activeNode === node.id;
      const points = [CENTER_POINT, node.position];
      const geometry = new THREE.BufferGeometry().setFromPoints(
        points.map((p) => new THREE.Vector3(...p))
      );
      return {
        geometry,
        color: isTarget ? node.color : "#475569",
        opacity: isTarget ? 0.8 : 0.22,
        lineWidth: isTarget ? 2.5 : 1,
      };
    });
  }, [activeNode]);

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
                linewidth: line.lineWidth,
              })
            )
          }
        />
      ))}
    </group>
  );
}

function Scene() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  return (
    <>
      <color attach="background" args={["#05070b"]} />
      <ambientLight intensity={0.45} />
      <pointLight position={[4, 4, 5]} intensity={35} color="#63e6ff" />
      <pointLight position={[-4, -3, 3]} intensity={20} color="#e7a977" />
      <pointLight position={[0, -4, -3]} intensity={15} color="#a78bfa" />
      <Stars radius={45} depth={15} count={1600} factor={1.5} saturation={0} />

      <IdeaCore activeNode={activeNode} />
      <ConnectionLines activeNode={activeNode} />

      {NODES.map((node) => (
        <ConstellationNode
          key={node.id}
          node={node}
          isActive={activeNode === node.id}
          onHover={setActiveNode}
          onClick={(id) => setActiveNode((prev) => (prev === id ? null : id))}
        />
      ))}

      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate
        autoRotateSpeed={activeNode ? 0.1 : 0.45}
        maxPolarAngle={Math.PI / 1.7}
        minPolarAngle={Math.PI / 2.8}
      />
    </>
  );
}

export default function LensScene() {
  return (
    <div className="relative h-[560px] w-full overflow-hidden rounded-3xl border border-white/10 bg-slate-950/40 backdrop-blur-sm">
      <div className="absolute left-5 top-5 z-10 text-[10px] tracking-[.25em] text-cyan-400">
        3D IDEA CONSTELLATION · 9 EVIDENCE NODES
      </div>
      <div className="absolute right-5 top-5 z-10 text-[10px] text-slate-500">
        INTERACTIVE · HOVER / ROTATE
      </div>
      <Canvas camera={{ position: [0, 0, 7.8], fov: 46 }}>
        <Scene />
      </Canvas>
      <div className="absolute bottom-4 left-5 z-10 text-[11px] text-slate-500">
        Crystalline Idea Core connected to research graph dimensions.
      </div>
    </div>
  );
}