from jira.client import JIRA
import graphviz  # for dot graph rendering/export
import os  # for environment variable
import argparse  # for parsing command line arguments


def label_for_node(type, key, summary, status):
    # TODO make color mapping configurable and robust
    # see: https://atlassian.design/foundations/color
    color = {
        "Task": {"fgcolor": "#DEEBFF", "bgcolor": "#2684FF"},
        "Story": {"fgcolor": "#E3FCEF", "bgcolor": "#00875A"},
        "Bug": {"fgcolor": "#FFEBE6", "bgcolor": "#DE350B"},
        "Epic": {"fgcolor": "#EAE6FF", "bgcolor": "#5243AA"},
        "To Do": {"fgcolor": "#42526e", "bgcolor": "#c1c7d0"},
        "In Progress": {"fgcolor": "#42526e", "bgcolor": "#c1c7d0"},
        "Blocked": {"fgcolor": "#42526e", "bgcolor": "#c1c7d0"},
        "Done": {"fgcolor": "#00875a", "bgcolor": "#b2d8b9"}
    }
    # see: https://renenyffenegger.ch/notes/tools/Graphviz/attributes/label/HTML-like/index
    return f'''< <table border="0"><tr>
        <td bgcolor="{color[type]["bgcolor"]}"><font color="{color[type]["fgcolor"]}">{type.upper()}</font></td>
        <td>{key}</td>
        <td>{summary}</td>
        <td bgcolor="{color[status]["bgcolor"]}"><font color="{color[status]["fgcolor"]}">{status.upper()}</font></td>
        </tr></table> >'''


def main():

    parser = argparse.ArgumentParser(
        description='Exports a JIRA issue graph as a Graphviz digraph.')
    parser.add_argument('--query', help="A valid JQL query providing issues.", required=True)
    parser.add_argument('--ignore-clones', action='store_true', default=False,
                        help='If set clone relations are being ignore.')
    parser.add_argument(
        '--output', type=argparse.FileType('w', encoding='UTF-8'), required=False, help="If defined the graph's source will be written to this file, otherwise to the command line.")
    args = parser.parse_args()

    server = os.getenv('JIRA_SERVER')
    if server is None:
        raise Exception("Missing requied environment variable 'JIRA_SERVER'")
    user = os.getenv('JIRA_USER')
    if server is None:
        raise Exception("Missing requied environment variable 'JIRA_USER'")
    apiKey = os.getenv('JIRA_PASSWORD')
    if server is None:
        raise Exception("Missing requied environment variable 'JIRA_PASSWORD'")

    jiraOptions = {'server': server}
    jira = JIRA(options=jiraOptions, basic_auth=(user, apiKey))

    dot = graphviz.Digraph()
    for issue in jira.search_issues(jql_str=args.query):
        key = issue.key
        status = issue.fields.status.name
        summary = issue.fields.summary
        issuetype = issue.fields.issuetype.name

        dot.node(
            issue.key,
            label_for_node(issuetype, key, summary, status),
            URL=f'{server}/browse/{issue.key}',
            color="black" if status.lower().find('block') == -1 else "red",
            shape="rect",
            style="rounded",
            fontname="sans-serif",
            tooltip=f"Click to open: {key} - {summary}")
        for link in issue.fields.issuelinks:
            if hasattr(link, "type"):
                if link.type.name == "Cloners" and args.ignore_clones:
                    continue
            if hasattr(link, "outwardIssue"):
                outwardIssue = link.outwardIssue
                color = "black" if link.type.outward.lower().find('block') == -1 else "red"
                dot.edge(issue.key, outwardIssue.key,
                         link.type.outward, color=color, fontname="sans-serif")
            # if hasattr(link, "inwardIssue"):
            #     inwardIssue = link.inwardIssue
            #     color = color_for_expression(link.type.inward)
            #     dot.edge(issue.key, inwardIssue.key,
            #              link.type.inward, color=color, fontname="sans-serif")

    if args.output:
        with open('graph.dot', 'w', encoding="utf-8") as f:
            f.write(dot.source)
    else:
        print(dot.source)


if __name__ == '__main__':
    main()
