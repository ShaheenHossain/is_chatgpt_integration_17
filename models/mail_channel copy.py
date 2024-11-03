# -*- coding: utf-8 -*-
# Copyright (c) 2020-Present InTechual Solutions. (<https://intechualsolutions.com/>)

from openai import OpenAI

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# LLM imports
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import OpenAI

class Channel(models.Model):
    _inherit = 'discuss.channel'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        rdata = super(Channel, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        chatgpt_channel_id = self.env.ref('is_chatgpt_integration.channel_chatgpt')
        user_chatgpt = self.env.ref("is_chatgpt_integration.user_chatgpt")
        partner_chatgpt = self.env.ref("is_chatgpt_integration.partner_chatgpt")
        author_id = msg_vals.get('author_id')
        chatgpt_name = str(partner_chatgpt.name or '') + ', '
        prompt = msg_vals.get('body')

        if not prompt:
            return rdata
        try:
            if author_id != partner_chatgpt.id and (chatgpt_name in msg_vals.get('record_name', '') or 'ChatGPT,' in msg_vals.get('record_name', '')) and self.channel_type == 'chat':
                res = self._get_chatgpt_response(prompt=prompt)
                self.with_user(user_chatgpt).message_post(body=res, message_type='comment', subtype_xmlid='mail.mt_comment')
            elif author_id != partner_chatgpt.id and msg_vals.get('model', '') == 'discuss.channel' and msg_vals.get('res_id', 0) == chatgpt_channel_id.id:
                res = self._get_chatgpt_response(prompt=prompt)
                chatgpt_channel_id.with_user(user_chatgpt).message_post(body=res, message_type='comment', subtype_xmlid='mail.mt_comment')

        except Exception as e:
            # Log or handle exceptions more specifically
            print("I am here in Exception of handle specifically")
            pass

        return rdata

    def _get_chatgpt_response(self, prompt):
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('is_chatgpt_integration.openapi_api_key')
        gpt_model_id = ICP.get_param('is_chatgpt_integration.chatgp_model')
        gpt_model = 'gpt-3.5-turbo'
        try:
            if gpt_model_id:
                gpt_model = self.env['chatgpt.model'].browse(int(gpt_model_id)).name
        except Exception as ex:
            gpt_model = 'gpt-3.5-turbo'
            print("I am here in Exception after gpt-3.5-turbo")
            pass
        try:
            print("I am starting the prompt")
            client = OpenAI(api_key=api_key)
            print("After initializing the client")
            messages = [{"role": "user", "content": prompt}]
            print("After initializing the messages")
            response = client.chat.completions.create(
                            messages=messages,
                            model='gpt-3.5-turbo'
                        )
            #GPT before
            # response = client.chat.completions.create(
            #                 messages=messages,
            #                 model=gpt_model,
            #                 temperature=0.0
            #             )
            # stream = client.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[{"role": "user", "content": "Say this is a test"}],
            #     stream=True,
            # )
            print("I am here after the response object")
            response_message = response.choices[0].message.content
            print("I am here lastly")
            print(response_message)
            return response_message
        except Exception as e:
            raise UserError(_(e))
