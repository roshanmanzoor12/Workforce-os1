export type TokenType =
  "bearer";

export type OAuthIntent =
  | "login"
  | "signup";


export interface AuthUser {
  avatar_source?: "auto" | "google" | "upload" | "preset" | "url" | "none";
  id: string;
  email: string;
  username: string;

  first_name:
    string | null;

  last_name:
    string | null;

  avatar_url:
    string | null;

  is_email_verified:
    boolean;

  is_active:
    boolean;

  is_locked:
    boolean;

  created_at:
    string;

  updated_at:
    string;
}


export interface LoginRequest {
  identifier: string;
  password: string;
  remember_me: boolean;
}


export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: TokenType;
  expires_in: number;
  user: AuthUser;
}


export interface RefreshTokenRequest {
  refresh_token: string;
}


export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: TokenType;
  expires_in: number;
}


export interface CurrentUserResponse {
  user: AuthUser;
}


export interface SignupRequest {
  email: string;
  username: string;
  password: string;

  confirm_password:
    string;

  first_name?:
    string | null;

  last_name?:
    string | null;
}


export interface SignupResponse {
  message: string;
  user: AuthUser;

  verification_required:
    boolean;
}


export interface VerifyEmailRequest {
  email: string;
  otp: string;
}


export interface ResendVerificationRequest {
  email: string;
}


export interface EmailVerificationResponse {
  message: string;
  verified: boolean;
  user: AuthUser | null;
}


export interface ForgotPasswordRequest {
  email: string;
}


export interface ForgotPasswordResponse {
  message: string;
  success: boolean;
}


export interface VerifyResetOtpRequest {
  email: string;
  otp: string;
}


export interface VerifyResetOtpResponse {
  message: string;
  verified: boolean;

  reset_token:
    string | null;

  reset_token_expires_in:
    number | null;
}


export interface ResetPasswordRequest {
  reset_token: string;
  new_password: string;
  confirm_password: string;
}


export interface ResetPasswordResponse {
  message: string;
  success: boolean;
}


export interface LogoutRequest {
  refresh_token: string;
}


export interface LogoutResponse {
  message: string;
  success: boolean;
}


export interface LogoutAllResponse {
  message: string;

  revoked_sessions:
    number;
}


export interface AuthSessionItem {
  id: string;

  device_name:
    string | null;

  user_agent:
    string | null;

  ip_address:
    string | null;

  expires_at:
    string;

  last_used_at:
    string | null;

  revoked_at:
    string | null;

  created_at:
    string;
}


export interface SessionsResponse {
  sessions:
    AuthSessionItem[];

  total: number;
}


export interface OAuthAuthorizationResponse {
  provider:
    | "google"
    | "github";

  authorization_url:
    string;
}


export interface OAuthCallbackResponse {
  access_token: string;
  refresh_token: string;
  token_type: TokenType;
  expires_in: number;

  user:
    AuthUser;

  provider:
    | "google"
    | "github";

  is_new_user:
    boolean;

  intent:
    OAuthIntent;

  remember_me:
    boolean;
}


export interface OAuthExchangeRequest {
  code: string;
}


export interface OAuthExchangeResponse
  extends TokenResponse {
  provider:
    | "google"
    | "github";

  is_new_user:
    boolean;

  intent:
    OAuthIntent;

  remember_me:
    boolean;
}