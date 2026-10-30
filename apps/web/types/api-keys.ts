export interface APIKeyPublic {
  id: string;

  workspace_id: string;

  created_by_user_id: string;

  name: string;

  key_prefix: string;

  scopes: string[];

  expires_at:
    string | null;

  revoked_at:
    string | null;

  revoked_by_user_id:
    string | null;

  last_used_at:
    string | null;

  created_at: string;

  updated_at: string;
}


export interface APIKeyCreateRequest {
  name: string;

  scopes: string[];

  expires_at?:
    string | null;
}


/**
 * Response returned after creating an API key.
 *
 * The plaintext secret is returned exactly once.
 * It must never be persisted by the frontend.
 */
export interface APIKeyCreateResponse {
  key: APIKeyPublic;

  secret: string;
}


/**
 * Response returned after rotating an API key.
 *
 * The new plaintext secret is returned exactly once.
 * The previous key secret must never be recoverable.
 */
export interface APIKeyRotateResponse {
  key: APIKeyPublic;

  secret: string;
}