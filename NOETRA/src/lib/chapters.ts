import type { Chapter } from '@/types/video'

/** Index of the chapter that contains `time`, or -1 when there are no chapters. */
export function findChapterIndex(time: number, chapters: Chapter[]): number {
  if (chapters.length === 0) return -1
  let index = 0
  for (let position = 0; position < chapters.length; position += 1) {
    if (time >= chapters[position].startTime) {
      index = position
    } else {
      break
    }
  }
  return index
}

/** Playback progress (0–1) through a chapter given the next chapter's start. */
export function getChapterProgress(time: number, chapter: Chapter, nextStart?: number): number {
  const end = nextStart ?? chapter.endTime ?? chapter.startTime
  const span = end - chapter.startTime
  if (span <= 0) return time >= chapter.startTime ? 1 : 0
  return Math.max(0, Math.min((time - chapter.startTime) / span, 1))
}
