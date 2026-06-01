using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class YunaProductionValidator
{
    private const string CharacterRoot = "Assets/Characters/YUNA";
    private static readonly string[] RequiredModels =
    {
        "yuna_production_lod0.fbx",
        "yuna_production_lod1.fbx",
        "yuna_production_lod2.fbx"
    };

    private static readonly string[] RequiredTextures =
    {
        "yuna_urp_basecolor.png",
        "yuna_urp_mask_metallic_occlusion_smoothness.png",
        "yuna_urp_normal.png",
        "yuna_urp_emission.png"
    };

    [MenuItem("Resonance Afterlight/Validate YUNA Production Asset")]
    public static void RunMenu()
    {
        Run();
    }

    public static void Run()
    {
        var errors = new List<string>();
        var warnings = new List<string>();
        var checkedItems = new List<string>();

        foreach (var model in RequiredModels)
        {
            var path = $"{CharacterRoot}/Models/{model}";
            var importer = AssetImporter.GetAtPath(path) as ModelImporter;
            if (importer == null)
            {
                errors.Add($"missing_model_importer:{path}");
                continue;
            }

            importer.importBlendShapes = true;
            importer.animationType = ModelImporterAnimationType.Human;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            importer.isReadable = false;
            importer.SaveAndReimport();

            checkedItems.Add($"model:{path}");

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab == null)
            {
                errors.Add($"model_load_failed:{path}");
                continue;
            }

            var renderers = prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            if (renderers.Length == 0)
                warnings.Add($"no_skinned_mesh_renderer_detected:{path}");

            var animator = prefab.GetComponentInChildren<Animator>(true);
            if (animator == null || animator.avatar == null)
                warnings.Add($"avatar_not_created:{path}");
            else if (!animator.avatar.isValid)
                errors.Add($"avatar_invalid:{path}");
            else
                checkedItems.Add($"avatar_valid:{path}");
        }

        foreach (var texture in RequiredTextures)
        {
            var path = $"{CharacterRoot}/Textures/{texture}";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null)
            {
                errors.Add($"missing_texture_importer:{path}");
                continue;
            }

            if (texture.Contains("_normal"))
                importer.textureType = TextureImporterType.NormalMap;
            importer.sRGBTexture = !(texture.Contains("_mask") || texture.Contains("_normal"));
            importer.alphaIsTransparency = texture.EndsWith(".png");
            importer.SaveAndReimport();
            checkedItems.Add($"texture:{path}");
        }

        var json = BuildJson(errors, warnings, checkedItems);
        var outPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../qa/unity/yuna_unity_validation_report.json"));
        Directory.CreateDirectory(Path.GetDirectoryName(outPath));
        File.WriteAllText(outPath, json, Encoding.UTF8);

        if (errors.Count > 0)
            throw new System.Exception("YUNA production validation failed. See " + outPath);
    }

    private static string BuildJson(List<string> errors, List<string> warnings, List<string> checkedItems)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"character_id\": \"yuna-white-sword\",");
        builder.AppendLine("  \"validator\": \"YunaProductionValidator\",");
        builder.AppendLine($"  \"status\": \"{(errors.Count == 0 ? "ok" : "failed")}\",");
        AppendArray(builder, "checked", checkedItems, true);
        AppendArray(builder, "warnings", warnings, true);
        AppendArray(builder, "errors", errors, false);
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static void AppendArray(StringBuilder builder, string name, List<string> values, bool comma)
    {
        builder.AppendLine($"  \"{name}\": [");
        for (var i = 0; i < values.Count; i++)
        {
            var suffix = i == values.Count - 1 ? "" : ",";
            builder.AppendLine($"    \"{values[i]}\"{suffix}");
        }
        builder.AppendLine($"  ]{(comma ? "," : "")}");
    }
}
