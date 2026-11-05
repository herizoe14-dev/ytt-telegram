-- Appliquée sur le projet Supabase « alice » (kvslcdvandyqlalvmwkx).
create table public.user_settings (
  chat_id    bigint primary key,
  mode       text not null default 'pivot' check (mode in ('pivot', 'direct')),
  debug      boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.user_settings is 'Réglages du bot Telegram Alice par conversation (chat_id Telegram).';

create function public.set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger user_settings_updated_at
before update on public.user_settings
for each row execute function public.set_updated_at();

-- RLS activé sans politique : seule la clé secrète (côté serveur) peut lire/écrire.
alter table public.user_settings enable row level security;
revoke all on public.user_settings from anon, authenticated;
