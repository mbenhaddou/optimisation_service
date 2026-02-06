import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from solution_routing import solution_routing_service
from solution_routing.solution_routing_model import SolutionRouting
from solution_routing.solution_routing_schema import SolutionRoutingCreate, SolutionRoutingStatus
from solution_routing.solution_routing_service import SolutionRoutingService


class TestPayloadService(unittest.TestCase):
    def setUp(self):
        self.solution_routing_service = SolutionRoutingService()
        self.db_session = MagicMock(spec=Session)
        self.solution_routing_create = MagicMock(spec=SolutionRoutingCreate)
        self.uuid = uuid4()
        self.solution_routing = MagicMock(spec=SolutionRouting)




    @patch('solution_routing.solution_routing_service.solution_routing_crud.get')
    def test_get_one_solution_routing(self, mock_get):
        mock_get.return_value = 'mocked solution_routing'
        result = self.solution_routing_service.get_one(self.db_session, self.uuid)
        mock_get.assert_called_once_with(self.db_session, self.uuid, False,False)
        self.assertEqual(result, 'mocked solution_routing')

    @patch('solution_routing.solution_routing_service.solution_routing_crud.get')
    def test_get_one_solution_routing_not_found(self, mock_get):
        mock_get.return_value = None
        with self.assertRaises(HTTPException):
            self.solution_routing_service.get_one(self.db_session, self.uuid)
    @patch('solution_routing.solution_routing_service.solution_routing_crud.create')
    def test_create_routing_solution(self, mock_create):
        mock_create.return_value = 'mocked solution_routing'
        result = self.solution_routing_service.create_routing_solution(self.db_session, self.solution_routing_create)
        mock_create.assert_called_once_with(self.db_session, self.solution_routing_create)
        self.assertEqual(result, 'mocked solution_routing')

    @patch('solution_routing.solution_routing_service.solution_routing_crud.get_multi')
    def test_get_multi_solution_routing(self, mock_get_multi):
        mock_get_multi.return_value = ['mocked solution_routing']
        result = self.solution_routing_service.get_multi(self.db_session, skip=0, limit=100, status=None, from_date=None,
                                                to_date=None, include_request=False)
        mock_get_multi.assert_called_once_with(self.db_session, 0, 100, None, None, None, False,False)
        self.assertEqual(result, ['mocked solution_routing'])

    @patch('solution_routing.solution_routing_service.solution_routing_crud.get')
    @patch('solution_routing.solution_routing_service.solution_routing_crud.remove')
    def test_delete_solution_routing(self, mock_remove, mock_get):
        mock_solution_routing = MagicMock()
        mock_solution_routing.status = "FINISHED"
        mock_get.return_value = mock_solution_routing
        mock_remove.return_value = 'mocked solution_routing'
        result = self.solution_routing_service.delete(self.db_session, self.uuid)
        mock_get.assert_called_once_with(self.db_session, self.uuid)
        mock_remove.assert_called_once_with(self.db_session, self.uuid)
        self.assertEqual(result, 'mocked solution_routing')

    @patch('solution_routing.solution_routing_service.solution_routing_crud.get')
    def test_delete_solution_routing_not_found(self, mock_get):
        mock_get.return_value = None
        with self.assertRaises(HTTPException):
            self.solution_routing_service.delete(self.db_session, self.uuid)

    @patch('solution_routing.solution_routing_service.solution_routing_crud.get')
    def test_delete_solution_routing_in_progress(self, mock_get):
        mock_solution_routing = MagicMock()
        mock_solution_routing.status = "IN_PROGRESS"
        mock_get.return_value = mock_solution_routing
        with self.assertRaises(HTTPException):
            self.solution_routing_service.delete(self.db_session, self.uuid)

    @patch('solution_routing.solution_routing_service.solution_routing_crud.remove_multi')
    def test_delete_multi_solution_routing(self, mock_remove_multi):
        mock_remove_multi.return_value = 5
        result = self.solution_routing_service.delete_multi(self.db_session, status=["FINISHED"], from_date="2022-01-01",
                                                   to_date="2022-12-31")
        mock_remove_multi.assert_called_once_with(self.db_session, ["FINISHED"], "2022-01-01", "2022-12-31")
        self.assertEqual(result, 5)

    @pytest.mark.asyncio
    @patch('solution_routing.solution_routing_service.solution_routing_crud.update', new_callable=AsyncMock)
    @patch('solution_routing.solution_routing_service.api.get_optimal_routes', new_callable=AsyncMock)
    async def test_start_optimization(mock_get_optimal_routes, mock_update):
        # Set up your mocks and test instance
        mock_get_optimal_routes.return_value = 'mocked results'
        test_solution_routing = SolutionRouting()
        test_solution_routing_service = solution_routing_service

        # Call the async function
        await test_solution_routing_service.start_optimization(test_solution_routing)

        # Validate the results
        mock_update.assert_called()
        mock_get_optimal_routes.assert_called_once_with(test_solution_routing)
        assert test_solution_routing.optimization_response == 'mocked results'
        assert test_solution_routing.status == SolutionRoutingStatus.finished.value

    @pytest.mark.asyncio
    @patch('solution_routing.solution_routing_service.solution_routing_crud.update', new_callable=AsyncMock)
    @patch('solution_routing.solution_routing_service.api.get_optimal_routes', new_callable=AsyncMock)
    async def test_start_optimization_exception(mock_get_optimal_routes, mock_update):
        # Set up your mocks and test instance
        mock_get_optimal_routes.side_effect = Exception('mocked exception')
        test_solution_routing = SolutionRouting()
        test_solution_routing_service = solution_routing_service

        # Call the async function with the expectation of an exception
        await test_solution_routing_service.start_optimization(test_solution_routing)

        # Validate the results
        mock_update.assert_called()
        mock_get_optimal_routes.assert_called_once_with(test_solution_routing)
        assert test_solution_routing.status == SolutionRoutingStatus.failed.value

if __name__ == '__main__':
    unittest.main()