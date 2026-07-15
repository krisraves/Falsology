export type Verdict = "truth" | "lie";
export type Difficulty = "easy" | "medium" | "hard";

export type EvidenceSource = {
  title: string;
  publisher: string;
  url: string;
  type: "primary" | "secondary";
  note?: string;
};

export type ClaimMedia = {
  type: "youtube";
  youtubeId: string;
  startSeconds: number;
  endSeconds: number;
  videoDurationSeconds: number;
  url: string;
  label: string;
  verifiedAt: string;
  sourceKind: string;
  directStatement: true;
  newsPackage: false;
};

export type Claim = {
  id: string;
  slug: string;
  caseNumber: string;
  person: string;
  personSlug: string;
  personRole: string;
  category: string;
  categorySlug: string;
  setting: string;
  date: string;
  claim: string;
  prompt: string;
  verdict: Verdict;
  classification: string;
  difficulty: Difficulty;
  shortExplanation: string;
  fullTruth: string;
  context: string;
  transcript: string;
  editorialBoundary: string;
  signals: string[];
  lesson: string;
  media: ClaimMedia;
  sources: EvidenceSource[];
  tags: string[];
  contentWarning?: string;
  reviewedAt: string;
};

export type GameAnswer = {
  claimId: string;
  answer: Verdict;
  correct: boolean;
  answeredAt: string;
};

export type PlayerState = {
  score: number;
  streak: number;
  bestStreak: number;
  answered: number;
  correct: number;
  history: GameAnswer[];
  saved: string[];
};
