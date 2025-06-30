#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025-06-30 13:12:46


import allure
import pytest
from utils.read_files_tools.get_yaml_data_analysis import GetTestCase
from utils.assertion.assert_control import Assert
from utils.requests_tool.request_control import RequestControl
from utils.read_files_tools.regular_control import regular
from utils.requests_tool.teardown_control import TearDownHandler


case_id = ['cece']
TestData = GetTestCase.case_data(case_id)
re_data = regular(str(TestData))


@allure.epic("User")
@allure.feature("cece")
class TestCece:

    @allure.story("cece")
    @pytest.mark.parametrize('in_data', eval(re_data), ids=[i['detail'] for i in TestData])
    def test_cece(self, in_data, case_skip):
        """
        :param :
        :return:
        """
        res = RequestControl(in_data).http_request()
        TearDownHandler(res).teardown_handle()
        Assert(assert_data=in_data['assert_data'],
               sql_data=res.sql_data,
               request_data=res.body,
               response_data=res.response_data,
               status_code=res.status_code).assert_type_handle()


if __name__ == '__main__':
    pytest.main(['test_test_cece.py', '-s', '-W', 'ignore:Module already imported:pytest.PytestWarning'])
