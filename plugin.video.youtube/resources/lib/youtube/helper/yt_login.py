import time

__author__ = 'bromix'


def process(mode, provider, context, re_match):
    if mode == 'out':
        access_manager = context.get_access_manager()
        client = provider.get_client(context)
        if access_manager.has_refresh_token():
            client.revoke(access_manager.get_refresh_token())
            pass
        provider.reset_client()
        access_manager.update_access_token(access_token='', refresh_token='')
        context.get_ui().refresh_container()
        pass
    elif mode == 'in':
        client = provider.get_client(context)
        json_data = client.generate_user_code()
        interval = int(json_data.get('interval', 5)) * 1000
        if interval > 60000:
            interval = 5000
            pass
        device_code = json_data['device_code']
        user_code = json_data['user_code']

        text = context.localize(provider.LOCAL_MAP['youtube.sign.go_to']) % '[B]youtube.com/activate[/B]'
        text += '[CR]%s [B]%s[/B]' % (context.localize(provider.LOCAL_MAP['youtube.sign.enter_code']), user_code)
        dialog = context.get_ui().create_progress_dialog(
            heading=context.localize(provider.LOCAL_MAP['youtube.sign.in']), text=text, background=False)

        steps = (10 * 60 * 1000) / interval  # 10 Minutes
        dialog.set_total(steps)
        for i in range(steps):
            dialog.update()
            json_data = client.get_device_token(device_code)
            if not 'error' in json_data:
                access_token = json_data.get('access_token', '')
                expires_in = time.time() + int(json_data.get('expires_in', 3600))
                refresh_token = json_data.get('refresh_token', '')
                if access_token and refresh_token:
                    provider.reset_client()
                    context.get_access_manager().update_access_token(access_token, expires_in, refresh_token)
                    context.get_ui().refresh_container()
                    break
                pass

            if dialog.is_aborted():
                break

            context.sleep(interval)
            pass
        dialog.close()
        pass
    pass
