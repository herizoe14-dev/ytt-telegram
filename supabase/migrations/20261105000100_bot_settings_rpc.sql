-- Appliquée sur le projet Supabase « alice » (kvslcdvandyqlalvmwkx).
-- Le bot utilise la clé publique + un secret dont seule l'empreinte SHA-256 est stockée.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table private.bot_secrets (
  name text primary key,
  secret_sha256 text not null
);
revoke all on private.bot_secrets from public, anon, authenticated;

-- Empreinte du secret actuel (le secret lui-même n'est jamais commité).
insert into private.bot_secrets (name, secret_sha256)
values ('telegram_bot', '4288337f0a0c6845628c895a76e5e8b87d67aa36e22634fa71cdac45214cb9a0');

create function private.check_bot_secret(p_secret text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_secret is null or not exists (
    select 1 from private.bot_secrets
    where name = 'telegram_bot'
      and secret_sha256 = encode(sha256(convert_to(p_secret, 'UTF8')), 'hex')
  ) then
    raise exception 'invalid bot secret' using errcode = '28000';
  end if;
end;
$$;
revoke all on function private.check_bot_secret(text) from public, anon, authenticated;

create function public.get_user_settings(p_bot_secret text, p_chat_id bigint)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  result jsonb;
begin
  perform private.check_bot_secret(p_bot_secret);
  select jsonb_build_object('mode', s.mode, 'debug', s.debug) into result
  from public.user_settings s where s.chat_id = p_chat_id;
  return result;
end;
$$;

create function public.set_user_settings(p_bot_secret text, p_chat_id bigint, p_mode text, p_debug boolean)
returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform private.check_bot_secret(p_bot_secret);
  insert into public.user_settings (chat_id, mode, debug)
  values (p_chat_id, p_mode, p_debug)
  on conflict (chat_id) do update set mode = excluded.mode, debug = excluded.debug;
end;
$$;

revoke all on function public.get_user_settings(text, bigint) from public, authenticated;
revoke all on function public.set_user_settings(text, bigint, text, boolean) from public, authenticated;
grant execute on function public.get_user_settings(text, bigint) to anon, service_role;
grant execute on function public.set_user_settings(text, bigint, text, boolean) to anon, service_role;
