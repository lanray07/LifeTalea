-- Source slots are keyed outside the database. The table never receives IP or receipt data.
create table lifetalea_private.rvs_source_quota (
  slot integer primary key check (slot between 0 and 4095),
  tokens double precision not null check (tokens between 0 and 3),
  updated_at timestamptz not null
);
alter table lifetalea_private.rvs_source_quota enable row level security;
revoke all on table lifetalea_private.rvs_source_quota from public, anon, authenticated;
grant select, insert, update on table lifetalea_private.rvs_source_quota to service_role;

create function public.lifetalea_consume_rvs_source_quota(source_slot integer)
returns boolean language plpgsql security invoker set search_path = '' as $$
declare admitted boolean;
begin
  if source_slot is null or source_slot < 0 or source_slot > 4095 then return false; end if;
  insert into lifetalea_private.rvs_source_quota as quota (slot, tokens, updated_at)
    values (source_slot, 2, clock_timestamp())
  on conflict (slot) do update
    set tokens = least(3, quota.tokens + greatest(0, extract(epoch from clock_timestamp() - quota.updated_at))) - 1,
        updated_at = clock_timestamp()
    where quota.tokens + greatest(0, extract(epoch from clock_timestamp() - quota.updated_at)) >= 1
    returning true into admitted;
  if admitted is distinct from true then return false; end if;
  return public.lifetalea_consume_rvs_quota();
end;
$$;
revoke all on function public.lifetalea_consume_rvs_source_quota(integer) from public, anon, authenticated;
grant execute on function public.lifetalea_consume_rvs_source_quota(integer) to service_role;
