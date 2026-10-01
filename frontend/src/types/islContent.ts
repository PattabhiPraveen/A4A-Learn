export type ISLAssetStatus =
  | "available"
  | "pending_review"
  | "unavailable";


export interface ISLLessonSegment {
  segment_id: string;
  heading: string;
  source_text: string;

  status: ISLAssetStatus;

  asset_type: string | null;
  asset_path: string | null;

  caption: string | null;
  validation_note: string | null;
}


export interface ISLLessonManifest {
  lesson_id: string;
  curriculum_id: string;
  title: string;

  status: ISLAssetStatus;

  segments: ISLLessonSegment[];

  available_segments: number;
  total_segments: number;

  message: string;
}