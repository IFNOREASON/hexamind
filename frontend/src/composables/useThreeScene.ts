import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

export interface ThreeContext {
  scene: THREE.Scene
  camera: THREE.PerspectiveCamera
  renderer: THREE.WebGLRenderer
  controls: OrbitControls
}

export function useThreeScene(containerId: string) {
  const context = ref<ThreeContext | null>(null) as Ref<ThreeContext | null>
  const animationCallbacks: Array<(delta: number) => void> = []
  let animationFrameId = 0
  const clock = new THREE.Clock()

  function init() {
    const container = document.getElementById(containerId)
    if (!container) return

    const width = container.clientWidth
    const height = container.clientHeight

    // Scene
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x0f172a, 0.003)

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 2000)
    camera.position.set(0, 80, 200)

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x000000, 0)
    container.appendChild(renderer.domElement)

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.minDistance = 50
    controls.maxDistance = 500
    controls.autoRotate = false
    controls.autoRotateSpeed = 0.5

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x334155, 1.5)
    scene.add(ambientLight)

    const pointLight1 = new THREE.PointLight(0x60a5fa, 2, 400)
    pointLight1.position.set(100, 100, 100)
    scene.add(pointLight1)

    const pointLight2 = new THREE.PointLight(0xa78bfa, 1.5, 400)
    pointLight2.position.set(-100, -50, -100)
    scene.add(pointLight2)

    // Background particles
    addBackgroundParticles(scene)

    context.value = { scene, camera, renderer, controls }

    // Resize handler
    const resizeObserver = new ResizeObserver(() => {
      if (!context.value) return
      const w = container.clientWidth
      const h = container.clientHeight
      context.value.camera.aspect = w / h
      context.value.camera.updateProjectionMatrix()
      context.value.renderer.setSize(w, h)
    })
    resizeObserver.observe(container)

    // Animation loop
    function animate() {
      animationFrameId = requestAnimationFrame(animate)
      const delta = clock.getDelta()
      controls.update()
      for (const cb of animationCallbacks) cb(delta)
      renderer.render(scene, camera)
    }
    animate()
  }

  function addBackgroundParticles(scene: THREE.Scene) {
    const count = 200
    const positions = new Float32Array(count * 3)
    for (let i = 0; i < count * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 600
    }
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const material = new THREE.PointsMaterial({
      color: 0x60a5fa,
      size: 1.5,
      transparent: true,
      opacity: 0.3,
    })
    scene.add(new THREE.Points(geometry, material))
  }

  function onAnimate(callback: (delta: number) => void) {
    animationCallbacks.push(callback)
  }

  function resetCamera() {
    if (!context.value) return
    const { camera, controls } = context.value
    camera.position.set(0, 80, 200)
    controls.target.set(0, 0, 0)
    controls.update()
  }

  function setAutoRotate(enabled: boolean) {
    if (!context.value) return
    context.value.controls.autoRotate = enabled
  }

  onMounted(init)

  onBeforeUnmount(() => {
    cancelAnimationFrame(animationFrameId)
    if (context.value) {
      context.value.renderer.dispose()
      context.value.controls.dispose()
    }
  })

  return {
    context,
    onAnimate,
    resetCamera,
    setAutoRotate,
  }
}
