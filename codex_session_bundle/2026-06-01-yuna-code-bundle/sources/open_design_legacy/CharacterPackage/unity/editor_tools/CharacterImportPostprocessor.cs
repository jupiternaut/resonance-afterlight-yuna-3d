using UnityEditor;

public class CharacterImportPostprocessor : AssetPostprocessor
{
    void OnPreprocessModel()
    {
        if (!assetPath.Contains("/Characters/") && !assetPath.Contains("/CharacterPackage/"))
            return;

        var importer = (ModelImporter)assetImporter;
        importer.useFileUnits = true;
        importer.bakeAxisConversion = true;
        importer.importBlendShapes = true;
        importer.isReadable = false;
        importer.optimizeGameObjects = true;
        importer.meshCompression = ModelImporterMeshCompression.Off;
    }

    void OnPreprocessTexture()
    {
        if (!assetPath.Contains("/Characters/") && !assetPath.Contains("/CharacterPackage/"))
            return;

        var importer = (TextureImporter)assetImporter;
        importer.isReadable = false;
        importer.maxTextureSize = assetPath.Contains("/Hero/") ? 2048 : 1024;

        var lower = assetPath.ToLowerInvariant();
        bool isNormal = lower.Contains("_n.") || lower.Contains("_normal.");
        bool isMask = lower.Contains("_orm.") || lower.Contains("_mask.") || lower.Contains("_mr.");
        importer.sRGBTexture = !(isNormal || isMask);

        if (lower.EndsWith(".png"))
            importer.alphaIsTransparency = true;

        if (isNormal)
            importer.textureType = TextureImporterType.NormalMap;
    }
}
