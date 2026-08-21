/* bloch.js — 布洛赫球组件（three.js）
 *
 * 功能：
 *   - 3D 球体 + X/Y/Z 坐标轴（着色区分）
 *   - 态矢量箭头（从球心到球面），z 轴 = |0⟩ 北极
 *   - OrbitControls 拖拽旋转视角
 *   - setState(theta, phi) 接口
 *   - applyGate(gate, params) 门旋转（X/Y/Z/H/S/T/RY/RZ）
 *
 * 数学：|ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩
 *       箭头方向 = (cosφ·sinθ, sinφ·sinθ, cosθ)
 * 用法：const b = Bloch.create(container);
 *       b.setState(Math.PI/2, 0);   // |+⟩
 *       b.applyGate("x");           // 绕 X 轴转 π
 */

const Bloch = (() => {
  let THREE = null;

  /* 加载 three.js（本地 vendor，不依赖外网）*/
  function loadThree() {
    return new Promise((resolve, reject) => {
      if (THREE) return resolve(THREE);
      if (window.THREE) { THREE = window.THREE; return resolve(THREE); }
      const script = document.createElement("script");
      script.src = "/static/vendor/three.min.js";
      script.onload = () => {
        const s2 = document.createElement("script");
        s2.src = "/static/vendor/OrbitControls.js";
        s2.onload = () => { THREE = window.THREE; resolve(THREE); };
        s2.onerror = () => reject(new Error("OrbitControls 加载失败"));
        document.head.appendChild(s2);
      };
      script.onerror = () => reject(new Error("three.min.js 加载失败"));
      document.head.appendChild(script);
    });
  }

  function create(container, opts = {}) {
    const size = opts.size || 320;
    const THREE_ = null;
    let scene, camera, renderer, controls;
    let arrow = null;      // 态矢量箭头
    let theta = 0, phi = 0;
    let animId = null;
    const readyCbs = [];
    let ready = false;

    function init(_THREE) {
      const t = _THREE;
      scene = new t.Scene();
      camera = new t.PerspectiveCamera(45, 1, 0.1, 100);
      camera.position.set(2.5, 1.8, 2.8);
      camera.lookAt(0, 0, 0);

      renderer = new t.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(size, size);
      container.appendChild(renderer.domElement);

      // 灯光
      scene.add(new t.AmbientLight(0xffffff, 0.7));
      const dl = new t.DirectionalLight(0xffffff, 0.6);
      dl.position.set(2, 3, 4);
      scene.add(dl);

      // 球体（半透明）
      const geo = new t.SphereGeometry(1, 48, 48);
      const mat = new t.MeshPhongMaterial({ color: 0x93c5fd, transparent: true, opacity: 0.25 });
      scene.add(new t.Mesh(geo, mat));

      // 经纬网格线
      const wire = new t.LineSegments(
        new t.WireframeGeometry(new t.SphereGeometry(1.002, 16, 16)),
        new t.LineBasicMaterial({ color: 0x93c5fd, transparent: true, opacity: 0.15 })
      );
      scene.add(wire);

      // 坐标轴 + 标签
      addAxis(t, "x", new t.Vector3(1.35, 0, 0), 0xff6b6b);
      addAxis(t, "y", new t.Vector3(0, 1.35, 0), 0x51cf66);
      addAxis(t, "z", new t.Vector3(0, 0, 1.35), 0x74c0fc);
      // |0⟩/|1⟩ 标签（z 轴两端）
      addLabel(t, "|0⟩", new t.Vector3(0, 0, 1.45), "#74c0fc");
      addLabel(t, "|1⟩", new t.Vector3(0, 0, -1.45), "#74c0fc");

      // 轨道控制
      controls = new t.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.1;

      // 初始箭头
      arrow = new t.ArrowHelper(new t.Vector3(0, 0, 1), new t.Vector3(0, 0, 0), 1, 0xffd43b, 0.25, 0.15);
      scene.add(arrow);

      animate();

      ready = true;
      readyCbs.forEach(cb => cb());
      readyCbs.length = 0;
    }

    function addAxis(t, name, dir, color) {
      const mat = new t.LineBasicMaterial({ color });
      const pts = [new t.Vector3(0, 0, 0), dir];
      const geo = new t.BufferGeometry().setFromPoints(pts);
      const line = new t.Line(geo, mat);
      line.name = "axis-" + name;
      scene.add(line);
      // 负半轴（虚线感：细一点）
      const pts2 = [new t.Vector3(0, 0, 0), dir.clone().multiplyScalar(-1)];
      const geo2 = new t.BufferGeometry().setFromPoints(pts2);
      const line2 = new t.Line(geo2, new t.LineBasicMaterial({ color, transparent: true, opacity: 0.35 }));
      line2.name = "axis-neg-" + name;
      scene.add(line2);
    }

    function addLabel(t, text, pos, color) {
      // 用 canvas 生成 sprite 文字
      const canvas = document.createElement("canvas");
      canvas.width = 128; canvas.height = 64;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "rgba(0,0,0,0)";
      ctx.fillRect(0, 0, 128, 64);
      ctx.font = "bold 36px sans-serif";
      ctx.fillStyle = color || "#fff";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(text, 64, 32);
      const tex = new t.CanvasTexture(canvas);
      const mat = new t.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
      const sprite = new t.Sprite(mat);
      sprite.scale.set(0.5, 0.25, 1);
      sprite.position.copy(pos);
      scene.add(sprite);
    }

    function animate() {
      animId = requestAnimationFrame(animate);
      if (controls) controls.update();
      if (renderer) renderer.render(scene, camera);
    }

    function setState(_theta, _phi) {
      theta = _theta; phi = _phi;
      // 箭头方向：x=cosφ·sinθ, y=sinφ·sinθ, z=cosθ
      const dir = new THREE.Vector3(
        Math.cos(phi) * Math.sin(theta),
        Math.sin(phi) * Math.sin(theta),
        Math.cos(theta)
      ).normalize();
      if (arrow) {
        arrow.setDirection(dir);
        arrow.setLength(1, 0.25, 0.15);
      }
    }

    function applyGate(gate, params) {
      // 计算门作用后的态，更新 theta/phi
      // |ψ'> = U|ψ>
      const ct = Math.cos(theta / 2), st = Math.sin(theta / 2);
      const cphi = Math.cos(phi), sphi = Math.sin(phi);
      // 复振幅 a=ct, b=e^{iφ}·st
      const br = st * cphi, bi = st * sphi;
      const ar = ct, ai = 0;

      let nr, ni, mr, mi; // 新 a, b
      if (gate === "x") { nr = br; ni = bi; mr = ar; mi = ai; }
      else if (gate === "y") { nr = bi; ni = -br; mr = -ai; mi = ar; }
      else if (gate === "z") { nr = ar; ni = ai; mr = -br; mi = -bi; }
      else if (gate === "h") {
        const s2 = 1 / Math.sqrt(2);
        nr = (ar + br) * s2; ni = (ai + bi) * s2;
        mr = (ar - br) * s2; mi = (ai - bi) * s2;
      }
      else if (gate === "s") {
        nr = ar; ni = ai;
        mr = -bi; mi = br;
      }
      else if (gate === "t") {
        nr = ar; ni = ai;
        const c = Math.cos(Math.PI / 4), s = Math.sin(Math.PI / 4);
        mr = br * c - bi * s; mi = br * s + bi * c;
      }
      else if (gate === "rz" || gate === "ry") {
        const ang = params || Math.PI / 2;
        if (gate === "rz") {
          nr = ar; ni = ai;
          const c = Math.cos(ang), s = Math.sin(ang);
          mr = br * c - bi * s; mi = br * s + bi * c;
        } else {
          const c = Math.cos(ang / 2), s = Math.sin(ang / 2);
          nr = ar * c - br * s; ni = ai * c - bi * s;
          mr = ar * s + br * c; mi = ai * s + bi * c;
        }
      } else {
        return;
      }
      // 归一化 → 新 θ, φ
      const na = Math.sqrt(nr * nr + ni * ni + mr * mr + mi * mi);
      if (na < 1e-12) return;
      const p0 = (nr * nr + ni * ni) / (na * na); // |a|^2
      const newTheta = 2 * Math.acos(Math.max(0, Math.min(1, Math.sqrt(p0))));
      let newPhi = Math.atan2(mi, mr);
      if (newPhi < 0) newPhi += 2 * Math.PI;
      setState(newTheta, newPhi);
    }

    function getState() { return { theta, phi }; }
    function dispose() {
      if (animId) cancelAnimationFrame(animId);
      if (renderer) { renderer.dispose(); if (renderer.domElement && renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement); }
    }

    loadThree().then(init).catch(e => {
      container.innerHTML = `<p style="color:#dc2626;padding:20px">布洛赫球加载失败：${e && e.message ? e.message : "three.js 资源缺失，请检查 /static/vendor/"}</p>`;
    });

    return {
      setState, applyGate, getState, dispose,
      onReady(cb) { if (ready) cb(); else readyCbs.push(cb); },
      get theta() { return theta; }, get phi() { return phi; },
    };
  }

  return { create, loadThree };
})();
