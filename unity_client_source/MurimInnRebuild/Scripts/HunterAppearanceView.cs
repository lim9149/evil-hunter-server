// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterAppearanceView : MonoBehaviour
    {
        [Header("Shared Animation")]
        public Animator sharedAnimator;

        [Header("Base Renderers")]
        public SpriteRenderer bodyRenderer;
        public SpriteRenderer hairRenderer;
        public SpriteRenderer outfitRenderer;
        public SpriteRenderer weaponRenderer;

        [Header("Mark Renderers (Sprite Resolver 또는 레이어 구조로 대체 가능)")]
        public SpriteRenderer headMarkRenderer;
        public SpriteRenderer shoulderMarkRenderer;
        public SpriteRenderer backMarkRenderer;

        [Header("Sprite Tables")]
        public Sprite[] hairSprites;      // hairId 사용
        public Sprite[] outfitSprites;    // outfitSpriteId 사용
        public Sprite[] weaponSprites;    // weaponSpriteId 사용
        public Sprite[] markSprites;      // ActiveMarkProfile.spriteId 사용

        public void ApplyProfile(HunterProfile profile, SharedAnimState animState)
        {
            if (profile == null)
            {
                return;
            }

            if (bodyRenderer != null)
            {
                bodyRenderer.color = profile.bodyTint;
            }

            ApplyIndexedSprite(hairRenderer, hairSprites, profile.hairId, Color.white);
            ApplyIndexedSprite(outfitRenderer, outfitSprites, profile.outfitSpriteId, Color.white);
            ApplyIndexedSprite(weaponRenderer, weaponSprites, profile.weaponSpriteId, Color.white);

            ClearMark(headMarkRenderer);
            ClearMark(shoulderMarkRenderer);
            ClearMark(backMarkRenderer);

            if (profile.activeMarks != null)
            {
                for (int i = 0; i < profile.activeMarks.Count; i++)
                {
                    ActiveMarkProfile mark = profile.activeMarks[i];
                    ApplyMark(mark);
                }
            }

            if (sharedAnimator != null)
            {
                sharedAnimator.SetInteger("State", (int)animState);
            }
        }

        private void ApplyMark(ActiveMarkProfile mark)
        {
            if (mark == null || mark.spriteId < 0 || markSprites == null || mark.spriteId >= markSprites.Length)
            {
                return;
            }

            SpriteRenderer target = mark.slot switch
            {
                MarkSlot.Head => headMarkRenderer,
                MarkSlot.Shoulder => shoulderMarkRenderer,
                MarkSlot.Back => backMarkRenderer,
                _ => null,
            };

            if (target == null)
            {
                return;
            }

            target.enabled = true;
            target.sprite = markSprites[mark.spriteId];
            target.color = mark.tint;
        }

        private static void ClearMark(SpriteRenderer renderer)
        {
            if (renderer == null)
            {
                return;
            }

            renderer.enabled = false;
            renderer.sprite = null;
            renderer.color = Color.clear;
        }

        private static void ApplyIndexedSprite(SpriteRenderer renderer, Sprite[] table, int index, Color tint)
        {
            if (renderer == null)
            {
                return;
            }

            if (table != null && index >= 0 && index < table.Length)
            {
                renderer.enabled = true;
                renderer.sprite = table[index];
                renderer.color = tint;
                return;
            }

            renderer.enabled = false;
            renderer.sprite = null;
        }
    }
}
