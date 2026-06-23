from flask import Blueprint

from app.models.result_file import ResultFile

result_files_bp = Blueprint(
    "result_files",
    __name__,
    url_prefix="/api/v1/result-files"
)


@result_files_bp.route("")
def list_result_files():

    files = ResultFile.query.order_by(
        ResultFile.created_at.desc()
    ).all()

    return {
        "count": len(files),
        "files": [
            item.to_dict()
            for item in files
        ]
    }


@result_files_bp.route("/order/<order_id>")
def files_by_order(order_id):

    files = ResultFile.query.filter_by(
        order_id=order_id
    ).order_by(
        ResultFile.created_at.desc()
    ).all()

    return {
        "count": len(files),
        "order_id": order_id,
        "files": [
            item.to_dict()
            for item in files
        ]
    }
