using UnityEngine;
using GLTFast;

public class LoadRuntimeGlb : MonoBehaviour
{
    [SerializeField] string glbUrl = "file:///D:/Assets/yuna_proxy_billboard.glb";

    async void Start()
    {
        var gltf = new GltfImport();
        var ok = await gltf.Load(glbUrl);

        if (!ok)
        {
            Debug.LogError("glTF load failed: " + glbUrl);
            return;
        }

        var root = new GameObject("YUNA_RuntimeProxy");
        await gltf.InstantiateMainSceneAsync(root.transform);
    }
}
