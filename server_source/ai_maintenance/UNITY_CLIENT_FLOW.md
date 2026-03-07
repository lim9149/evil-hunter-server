# UNITY CLIENT FLOW

## Minimum playable flow
1. Guest login
2. Create or fetch hunter
3. Enter combat
4. Show combat result
5. Preview offline reward
6. Collect offline reward

## Recommended scene order
- LoginScene
- VillageScene
- HunterScene
- BattleScene
- RewardPopup

## DTOs Unity should model first
- health response
- auth token response
- hunter create/read response
- combat fight response
- offline preview/collect response

## Rule
Unity should treat server as authority for progression and reward outcomes.
