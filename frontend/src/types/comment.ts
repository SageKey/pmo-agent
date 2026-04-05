export interface Comment {
  id: number;
  project_id: string;
  author: string | null;
  body: string;
  comment_type: string | null;
  created_at: string | null;
  updated_at: string | null;
}
