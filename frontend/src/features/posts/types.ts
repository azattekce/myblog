export interface CategoryRef {
  id: string;
  name: string;
  slug: string;
}

export interface PostSummary {
  id: string;
  title: string;
  slug: string;
  summary: string;
  status: 'draft' | 'published';
  author_name: string;
  cover_image_url: string | null;
  reading_time: number;
  comment_count: number;
  tags: string[];
  category: CategoryRef | null;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface PostDetail extends PostSummary {
  content: string;
  view_count?: number;
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface Category extends CategoryRef {
  description: string;
  post_count: number;
}

export interface PostWrite {
  title: string;
  summary: string;
  content: string;
  slug?: string | null;
  category_id?: string | null;
  tags: string[];
  cover_image_url?: string | null;
  publish?: boolean;
}

export interface PostStats {
  total: number;
  published: number;
  drafts: number;
  comments: number;
}
