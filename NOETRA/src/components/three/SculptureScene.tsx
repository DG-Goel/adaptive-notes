import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment, Float, Lightformer } from '@react-three/drei'
import * as THREE from 'three'

/* ------------------------------------------------------------------ */
/*  The glass ribbon mesh (geometry, material & motion unchanged)      */
/* ------------------------------------------------------------------ */

function GlassRibbon({
  variant = 'hero',
  inView,
}: {
  variant?: 'hero' | 'mini'
  inView: boolean
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const targetX = useRef(0)
  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  useFrame((state, delta) => {
    const mesh = meshRef.current
    if (!mesh) return

    // Pause rotation when offscreen for performance
    if (!inView) return

    const speed = reduceMotion ? 0 : variant === 'mini' ? 0.25 : 0.4
    mesh.rotation.y += delta * speed

    // Smooth spring-like convergence toward target tilt
    const lerpFactor = reduceMotion ? 1 : 0.06
    mesh.rotation.x = THREE.MathUtils.lerp(mesh.rotation.x, targetX.current, lerpFactor)

    // Subtle breathing scale
    if (!reduceMotion) {
      const t = state.clock.elapsedTime
      const s = 1 + Math.sin(t * 0.8) * 0.008
      mesh.scale.setScalar(s)
    }
  })

  return (
    <mesh
      ref={meshRef}
      rotation={[0.3, 0.4, 0]}
      onPointerMove={(e) => {
        if (reduceMotion) return
        targetX.current = (e.point.y / 3) * 0.4
      }}
      onPointerOut={() => {
        targetX.current = 0
      }}
    >
      <torusKnotGeometry args={[1, 0.32, 256, 48, 2, 3]} />
      <meshPhysicalMaterial
        // Near-colourless crystal base — clear white with a whisper of warmth
        color="#FCFBF9"
        metalness={0}
        roughness={0.015}
        transmission={1}
        thickness={1.5}
        ior={1.52}
        clearcoat={1}
        clearcoatRoughness={0.02}
        envMapIntensity={2.6}
        // Faint champagne absorption only in the thickest volumes
        attenuationColor="#F3E2C4"
        attenuationDistance={8}
        // Delicate thin-film shimmer for crisp, jewel-like reflections
        iridescence={0.25}
        iridescenceIOR={1.32}
        iridescenceThicknessMinimum={120}
        iridescenceThicknessMaximum={420}
        // Subtle chromatic dispersion — gives the glass real optical depth
        dispersion={2}
        specularIntensity={1}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

/* ------------------------------------------------------------------ */
/*  Lazy-loaded scene — the only module that pulls in three.js         */
/* ------------------------------------------------------------------ */

export interface SculptureSceneProps {
  variant: 'hero' | 'mini'
  inView: boolean
}

export default function SculptureScene({ variant, inView }: SculptureSceneProps) {
  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0, 4.5], fov: 38 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      frameloop={inView ? 'always' : 'demand'}
    >
      <ambientLight intensity={0.3} />
      {/* Cool-white key light — crisp crystal highlights */}
      <directionalLight position={[5, 6, 5]} intensity={1.5} color="#FFFFFF" />
      {/* Champagne accent — subtle warm sparkle */}
      <pointLight position={[-4, 2, 3]} intensity={1.6} color="#E8C79A" />
      {/* Burnt-orange brand accent, restrained */}
      <pointLight position={[3, -2, -4]} intensity={0.6} color="#D65A16" />
      {/* Cool rim/back light — keeps the glass reading as clear, not beige */}
      <pointLight position={[0, 3, -6]} intensity={1.1} color="#C9D8E8" />
      <spotLight
        position={[0, 8, 4]}
        angle={0.5}
        penumbra={1}
        intensity={1.4}
        color="#FFFFFF"
        castShadow={false}
      />

      <Float
        speed={variant === 'mini' ? 1.2 : 1.6}
        rotationIntensity={0.15}
        floatIntensity={variant === 'mini' ? 0.4 : 0.7}
      >
        <GlassRibbon variant={variant} inView={inView} />
      </Float>

      <Environment resolution={128}>
        <Lightformer intensity={3} position={[0, 5, 4]} rotation={[Math.PI / 4, 0, 0]} scale={[8, 3, 1]} />
        <Lightformer intensity={2} position={[-5, 1, 0]} rotation={[0, -Math.PI / 2, 0]} scale={[3, 6, 1]} />
        <Lightformer intensity={1.5} position={[0, 2, -5]} rotation={[0, Math.PI, 0]} scale={[6, 3, 1]} />
      </Environment>
    </Canvas>
  )
}
