# Cloth Seam Surface v1 Iteration Log

## Round 1: `minimal`

- Hypothesis: Conservative pass: preserve the v0 front silhouette and reduce side-volume changes to the minimum readable shell.
- Changed parameters:
  - thickness_scale: 0.58
  - curvature_scale: 0.7
  - cape_drape_bias: 0.0
  - skirt_drape_bias: 0.0
  - seam_emphasis: 0.85
- Screenshots generated:
  - candidate_front: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_candidate_front.png
  - overlay_front: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_overlay_front.png
  - yaw15: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_yaw15.png
  - yaw30: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_yaw30.png
  - side: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_side.png
  - wire: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_wire.png
  - exploded: CharacterPackage/semantic_layer_v9_cloth/variants/minimal/validation_ci/yuna_semantic_layer_v9_cloth_minimal_validation_exploded.png
- Metrics:
  - cloth_mask_purity_ratio: 1.0
  - non_cloth_texture_leak_ratio: 0.0
  - cloth_side_volume_present: True
  - cloth_edge_thickness_present: True
  - cloth_panel_curvature_score: 0.138019
  - cloth_drape_depth_span: 1.05545
  - silhouette_readability_front: 0.88
  - yaw30_cloth_readability: 0.68492
  - side_volume_readability: 0.732199
- Failure mode: May remain too close to the flat-sheet v0 side read.
- Next adjustment: If preferred, raise cape depth separation without changing the front silhouette.

## Round 2: `heroic`

- Hypothesis: Cinematic pass: push cape and skirt drape for the strongest readable silhouette while staying candidate-only.
- Changed parameters:
  - thickness_scale: 1.05
  - curvature_scale: 1.38
  - cape_drape_bias: 0.07
  - skirt_drape_bias: 0.04
  - seam_emphasis: 1.05
- Screenshots generated:
  - candidate_front: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_candidate_front.png
  - overlay_front: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_overlay_front.png
  - yaw15: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_yaw15.png
  - yaw30: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_yaw30.png
  - side: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_side.png
  - wire: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_wire.png
  - exploded: CharacterPackage/semantic_layer_v9_cloth/variants/heroic/validation_ci/yuna_semantic_layer_v9_cloth_heroic_validation_exploded.png
- Metrics:
  - cloth_mask_purity_ratio: 1.0
  - non_cloth_texture_leak_ratio: 0.0
  - cloth_side_volume_present: True
  - cloth_edge_thickness_present: True
  - cloth_panel_curvature_score: 0.308569
  - cloth_drape_depth_span: 1.26805
  - silhouette_readability_front: 0.96
  - yaw30_cloth_readability: 0.943997
  - side_volume_readability: 0.858971
- Failure mode: May overstate cape volume for a DCC proxy and needs manual art review.
- Next adjustment: If preferred, keep the cape sweep but reduce skirt depth bias.

## Round 3: `technical`

- Hypothesis: Sci-fi pass: emphasize seam guides and harder panel separation for DCC readability.
- Changed parameters:
  - thickness_scale: 0.86
  - curvature_scale: 0.96
  - cape_drape_bias: 0.025
  - skirt_drape_bias: 0.015
  - seam_emphasis: 1.45
- Screenshots generated:
  - candidate_front: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_candidate_front.png
  - overlay_front: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_overlay_front.png
  - yaw15: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_yaw15.png
  - yaw30: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_yaw30.png
  - side: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_side.png
  - wire: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_wire.png
  - exploded: CharacterPackage/semantic_layer_v9_cloth/variants/technical/validation_ci/yuna_semantic_layer_v9_cloth_technical_validation_exploded.png
- Metrics:
  - cloth_mask_purity_ratio: 1.0
  - non_cloth_texture_leak_ratio: 0.0
  - cloth_side_volume_present: True
  - cloth_edge_thickness_present: True
  - cloth_panel_curvature_score: 0.211425
  - cloth_drape_depth_span: 1.144
  - silhouette_readability_front: 0.92
  - yaw30_cloth_readability: 0.801996
  - side_volume_readability: 0.79168
- Failure mode: May look too diagrammatic for the final art direction.
- Next adjustment: If preferred, keep seam anchors but reduce cyan guide dominance.

