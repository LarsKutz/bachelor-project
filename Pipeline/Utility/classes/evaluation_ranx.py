import json
import os
from typing import List, Any, Dict
from reranking import Reranker
from utils import ChunkingType, RetrieverType, RerankerType
from ranx import Qrels, Run, compare
from langchain_core.documents import Document
from collections import defaultdict

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("cohere").setLevel(logging.WARNING)



class EvaluationRanx:
    def __init__(self, metrics: list=["ndcg@3", "mrr@3", "map@3"]):
        """ https://amenra.github.io/ranx/metrics/
        """
        self.metrics = metrics
    
    
    def save_as_json(self, data: Any, save_path: str, default_name: str) -> None:
        path = save_path if save_path.endswith(".json") else os.path.join(save_path, default_name)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise e
    
    
    def create_qrels(
        self, 
        rel_ids: List[int], 
        rel_scores: List[int], 
        dict_key_name: str="q", 
        save_path: str=None
    ) -> Qrels:
        if len(rel_ids) != len(rel_scores):
            raise ValueError(f"The length of rel_ids and rel_scores should be the same. Current shapes: ({len(rel_ids)}, {len(rel_scores)})")
        
        qrels_dict = {}
        qrels_dict[dict_key_name] = {f"d_{rel_id}": rel_score for rel_id, rel_score in zip(rel_ids, rel_scores)}
        
        if save_path is not None:
            self.save_as_json(qrels_dict, save_path, "qrels.json")
        
        return Qrels(qrels_dict)
    
    
    def create_runs(
        self, 
        docs_list: List[List[Document]], 
        run_names: List[str], 
        dict_key_name: str="q", 
        save_paths: List[str]=None
    ) -> List[Run]:
        if len(docs_list) != len(run_names):
            raise ValueError(f"The length of docs_list and run_names should be the same. Current shapes: ({len(docs_list)}, {len(run_names)})")
        
        runs_list = []
        for docs, run_name in zip(docs_list, run_names):
            run_dict = {}
            run_dict[dict_key_name] = {
                f"d_{doc.metadata['id']}": doc.metadata["relevance_score"] if "relevance_score" in doc.metadata 
                else doc.metadata['score'] 
                for doc in docs
            }
            runs_list.append(Run(run_dict, run_name))
        
        if save_paths is not None:
            if len(save_paths) != len(runs_list):
                raise ValueError(f"The length of save_path and runs_list should be the same. Current shapes: ({len(save_paths)}, {len(runs_list)})")
            for run, save_path in zip(runs_list, save_paths):
                self.save_as_json(run.to_dict(), save_path, f"run_{run.name}.json")
        
        return runs_list
    
    
    def compare_query(self, qrels: Qrels, runs: List[Run], metrics: List[str]=None, save_path: str=None) -> Any:
        """ Compare over one query with multiple runs (different reranking algorithms).
        """
        report = compare(qrels=qrels, runs=runs, metrics=metrics if metrics is not None else self.metrics)
        
        if save_path is not None:
            self.save_as_json(report.to_dict(), save_path, "report.json")
        
        return report
    
    
    def compare_all_queries_base(
            self, 
            queries: List[Dict[str, Any]],
            qrels_path: List[str],
            n_retriever: int=40, 
            chunking_types: List[ChunkingType]=[ChunkingType.BASIC, ChunkingType.TITLE], 
            reranker_types: List[RerankerType]=[RerankerType.COHERE, RerankerType.FLASHRANK], 
            metrics: List[str]=None,
            save_paths: List[str]=None,
            print_progress: bool=True
    ) -> List[Any]:
        if len(chunking_types) != len(save_paths) and save_paths is not None:
            raise ValueError(f"The length of chunking_types and save_paths should be the same. Current shapes: ({len(chunking_types)}, {len(save_paths)})")
        
        reports = []
        for i, chunking_type in enumerate(chunking_types):
            if print_progress:
                print(f"Processing chunking type: {chunking_type.value}...")
            
            # initialize reranker and qrels_dict
            reranker = Reranker(n_retriever=n_retriever, n_reranker=n_retriever, chunking_type=chunking_type)
            qrels_dict, runs_lists = {}, [{} for _ in range(len(reranker_types)+1)]
            
            # run loop over all queries
            for question_dict in queries:
                q_id = question_dict["id"]
                qrels_file_id = q_id+1
                question = question_dict["question"]
                
                if print_progress:
                    print(f"Processing query with id: {q_id}...")
                
                # get qrels
                qrels_file_path = os.path.join(qrels_path, f"q_{qrels_file_id}_qrels_base_{chunking_type.value}.json")
                qrels_dict.update(Qrels.from_file(qrels_file_path).to_dict())
                
                # get docs for each reranker type
                reranker_docs = []  # -> [base_docs, reranker1_docs, reranker2_docs, ...]
                for reranker_type in reranker_types:
                    if not reranker_docs:
                        # append reranker docs
                        reranker_docs.append(reranker.rerank(question, RetrieverType.BASE_SCORES, reranker_type))  
                        # append base docs at the beginning
                        reranker_docs.insert(0, reranker.documents)
                    else:
                        # append second if there are more than one reranker types
                        reranker_docs.append(reranker.rerank_with_documents(question, reranker_docs[0], reranker_type))
                
                # [
                #     {q_1: {d_0: 0.8453453454, ...}, ...},    # base
                #     {q_1: {d_2: 0.9564562234, ...}, ...},    # reranker1
                #     {q_1: {d_1: 0.6456456456, ...}, ...},    # reranker2
                #     ...                                           # ...
                # ]
                # create run_dict for each reranker type
                for j, docs in enumerate(reranker_docs):
                    run_dict = {                                                    # relevance_score is used by reranker, score is used by retriever
                        f"q_{qrels_file_id}": {f"d_{doc.metadata['id']}": doc.metadata["relevance_score"] if "relevance_score" in doc.metadata else doc.metadata['score'] for doc in docs},
                    }
                    runs_lists[j].update(run_dict)
                    
            # compare all runs and compute average over all queries
            report = compare(
                qrels=Qrels(qrels_dict),
                runs=[Run(run_dict, name) for run_dict, name in zip(runs_lists, ["base"]+[reranker_type.value for reranker_type in reranker_types])],
                metrics=metrics if metrics is not None else self.metrics,
            )
            reports.append(report)
            
            if save_paths is not None:
                self.save_as_json(report.to_dict(), save_paths[i], f"report_base_{chunking_type.value}_{n_retriever}.json")
        
        return reports
    
    
    def compute_average_with_reports(
        self, 
        report_paths: List[str],
        n_retriever: int=40,
        chunking_types: List[ChunkingType]=[ChunkingType.BASIC, ChunkingType.TITLE], 
        reranker_types: List[RerankerType]=[RerankerType.COHERE, RerankerType.FLASHRANK],
        metrics: List[str]=["ndcg@3", "ndcg@5","mrr@3","mrr@5","map@3","map@5"],
        save_paths: List[str]=None,
    ):
        if len(chunking_types) != len(report_paths):
            raise ValueError(f"The length of chunking_types and report_paths should be the same. Current shapes: ({len(chunking_types)}, {len(report_paths)})")
        if len(chunking_types) != len(save_paths) and save_paths is not None:
            raise ValueError(f"The length of chunking_types and save_paths should be the same. Current shapes: ({len(chunking_types)}, {len(save_paths)})")
        
        reports = []
        for i, (report_path, chunking_type) in enumerate(zip(report_paths, chunking_types)):
            all_files = [file for file in os.listdir(report_path) if "report" in file]
            score_dict = defaultdict(dict)
            
            for file in all_files:
                with open(os.path.join(report_path, file), "r", encoding="utf-8") as f:
                    report = json.load(f)
                for name in ["base"]+[r.value for r in reranker_types]:
                    for metric in metrics:
                        score_dict[name][metric] = report[name]["scores"][metric] + score_dict[name].get(metric, 0)
            
            saving_dict = {
                name: {"scores": {metric: score_dict[name][metric]/len(all_files) for metric in metrics}} for name in ["base"]+[r.value for r in reranker_types]
            }
            
            full_dict = {
                "metrics": metrics,
                "model_names": ["base"]+[r.value for r in reranker_types],
                **saving_dict
            }
            
            reports.append(full_dict)
            
            if save_paths is not None:
                self.save_as_json(full_dict, save_paths[i], f"report_{chunking_type.value}_{n_retriever}.json")
        
        return reports



if __name__ == "__main__":
    e = EvaluationRanx()
    e.compute_average_for_mq(
        report_paths=["D://Studium//Informatik//Module//Bachelorarbeit//Project//Pipeline//5-Reranken//Evaluation//Data//json//seed_1//mq_basic", "D://Studium//Informatik//Module//Bachelorarbeit//Project//Pipeline//5-Reranken//Evaluation//Data//json//seed_1//mq_by_title"],
        chunking_types=[ChunkingType.BASIC, ChunkingType.TITLE],
        save_paths=["asd", "asd"],
    )