import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Sphere, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { Location } from '../types';
import './GlobeView.css';

interface GlobeViewProps {
  onLocationSelect: (location: Location) => void;
}

function Earth() {
  const meshRef = useRef<THREE.Mesh>(null);
  const cloudsRef = useRef<THREE.Mesh>(null);
  
  // Load realistic Earth textures from CORS-enabled CDN
  const [colorMap, cloudsMap] = useLoader(THREE.TextureLoader, [
    'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg',
    'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_clouds_1024.png'
  ]);
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.001;
    }
    if (cloudsRef.current) {
      cloudsRef.current.rotation.y += 0.0012; // Clouds rotate slightly faster
    }
  });

  return (
    <group>
      {/* Main Earth sphere with realistic texture */}
      <Sphere ref={meshRef} args={[2, 64, 64]}>
        <meshStandardMaterial
          map={colorMap}
          metalness={0.1}
          roughness={0.8}
        />
      </Sphere>
      
      {/* Atmosphere glow */}
      <Sphere args={[2.12, 64, 64]}>
        <meshBasicMaterial
          color="#88ccff"
          transparent
          opacity={0.2}
          side={THREE.BackSide}
        />
      </Sphere>
      
      {/* Cloud layer with real cloud texture */}
      <Sphere ref={cloudsRef} args={[2.03, 64, 64]}>
        <meshStandardMaterial
          map={cloudsMap}
          transparent
          opacity={0.3}
          depthWrite={false}
        />
      </Sphere>
    </group>
  );
}

const GlobeView: React.FC<GlobeViewProps> = ({ onLocationSelect }) => {
  const [showPrompt, setShowPrompt] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowPrompt(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  const handlePointerDown = (e: React.PointerEvent) => {
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    setIsDragging(false);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    const distance = Math.sqrt(
      Math.pow(e.clientX - dragStartRef.current.x, 2) +
      Math.pow(e.clientY - dragStartRef.current.y, 2)
    );
    if (distance > 5) {
      setIsDragging(true);
    }
  };

  const handleGlobeClick = () => {
    // Only register click if not dragging
    if (!isDragging) {
      onLocationSelect({
        lat: 25.0330,
        lng: 121.5654,
        name: 'Taipei City Center'
      });
    }
  };

  return (
    <div className="globe-container">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        onClick={handleGlobeClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      >
        {/* Brighter ambient light */}
        <ambientLight intensity={0.6} />
        
        {/* Main directional light (sun) - brighter */}
        <directionalLight position={[5, 3, 5]} intensity={2.2} />
        
        {/* Fill light to soften shadows - brighter */}
        <pointLight position={[-5, 0, -5]} intensity={0.5} />
        
        {/* Back rim light for depth */}
        <pointLight position={[0, 5, -5]} intensity={0.4} color="#88ccff" />
        
        <Stars
          radius={100}
          depth={50}
          count={5000}
          factor={4}
          saturation={0}
          fade
        />
        <React.Suspense fallback={null}>
          <Earth />
        </React.Suspense>
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          minDistance={3}
          maxDistance={10}
        />
      </Canvas>
      
      {showPrompt && (
        <div className="globe-prompt fade-in">
          <h1>TaipeiSim</h1>
          <p>Historical Traffic Simulation Router</p>
          <p className="subtitle">Click or search to begin your journey to Taipei</p>
        </div>
      )}
    </div>
  );
};

export default GlobeView;
        