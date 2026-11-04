-- Dedicated global quota, no account/receipt/IP data. Existing application objects are untouched.
create schema lifetalea_private;
revoke all on schema lifetalea_private from public, anon, authenticated;
grant usage on schema lifetalea_private to service_role;
create table lifetalea_private.rvs_quota (
  id boolean primary key default true check(id),
  tokens double precision not null check(tokens between 0 and 5),
  updated_at timestamptz not null
);
alter table lifetalea_private.rvs_quota enable row level security;
revoke all on table lifetalea_private.rvs_quota from public, anon, authenticated;
grant select, update on lifetalea_private.rvs_quota to service_role;
insert into lifetalea_private.rvs_quota values(true,5,clock_timestamp());
create function public.lifetalea_consume_rvs_quota() returns boolean
language plpgsql security invoker set search_path=''
as $$
declare available double precision; previous timestamptz; instant timestamptz;
begin
  select tokens,updated_at into available,previous from lifetalea_private.rvs_quota where id=true for update;
  if not found then return false; end if;
  instant:=clock_timestamp();
  available:=least(5,available+greatest(0,extract(epoch from instant-previous))*5);
  if available<1 then
    update lifetalea_private.rvs_quota set tokens=available,updated_at=instant where id=true;
    return false;
  end if;
  update lifetalea_private.rvs_quota set tokens=available-1,updated_at=instant where id=true;
  return true;
end;
$$;
revoke all on function public.lifetalea_consume_rvs_quota() from public,anon,authenticated;
grant execute on function public.lifetalea_consume_rvs_quota() to service_role;
