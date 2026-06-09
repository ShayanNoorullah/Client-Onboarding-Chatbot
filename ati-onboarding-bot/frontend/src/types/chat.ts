export type Stage =
  | "greeting"
  | "consent"
  | "identity"
  | "requirements"
  | "clarify"
  | "summarise"
  | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ServerMessage {
  type: "message";
  role: "assistant";
  content: string;
  stage?: Stage;
  done?: boolean;
  ref_id?: string | null;
  suggestions?: string[];
  consent_given?: boolean;
  client_name?: string | null;
  assets_count?: number;
}

export interface UploadedAsset {
  filename: string;
  preview?: string;
}
