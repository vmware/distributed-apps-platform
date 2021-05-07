import React, { Component } from 'react'
import { Col, Row} from 'antd';
import axios from 'axios';
import { Redirect } from 'react-router-dom';
import { baseUrl } from '../../config';

import { useContext, useState, useEffect, useRef } from 'react';
import { Table, Input, Form } from 'antd';


import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap4.min.css"; // use Theme(s)
import { ReactTabulator, reactFormatter } from 'react-tabulator'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { library } from "@fortawesome/fontawesome-svg-core";
import {faApple, faWindows, faUbuntu} from "@fortawesome/free-brands-svg-icons"
import {faPencilAlt} from "@fortawesome/free-solid-svg-icons"

library.add(faWindows);
library.add(faUbuntu);
library.add(faApple);
library.add(faPencilAlt)

const EditableContext = React.createContext(null);

const EditableRow = ({ index, ...props }) => {
    const [form] = Form.useForm();
    return (
      <Form form={form} component={false}>
        <EditableContext.Provider value={form}>
          <tr {...props} />
        </EditableContext.Provider>
      </Form>
    );
  };

const EditableCell = ({
    title,
    editable,
    children,
    dataIndex,
    record,
    handleSave,
    ...restProps
  }) => {
    const [editing, setEditing] = useState(false);
    const inputRef = useRef(null);
    const form = useContext(EditableContext);
    useEffect(() => {
      if (editing && record.key === "IP") {
        inputRef.current.focus();
      }
    }, [editing, record]);

    const toggleEdit = () => {
      setEditing(!editing);
      form.setFieldsValue({
        [dataIndex]: record[dataIndex],
      });
    };

    const save = async () => {
      try {
        console.log("__________________________")
        console.log(record)
        const values = await form.validateFields();
        toggleEdit();
        handleSave({ ...record, ...values });
      } catch (errInfo) {
        console.log('Save failed:', errInfo);
      }
    };

    let childNode = children;

    if (editable) {
      childNode = editing && record.key === "IP" ? (
        <Form.Item
          style={{
            margin: 0,
          }}
          name={dataIndex}
          rules={[
            {
              required: true,
              message: `${title} is required.`,
            },
          ]}
        >
          <Input ref={inputRef} onPressEnter={save} onBlur={save} />
        </Form.Item>
      ) : (
        <div
          className="editable-cell-value-wrap"
          style={{
            paddingRight: 24,
          }}
          onClick={toggleEdit}
        >
          {children}
        </div>
      );
    }

    return <td {...restProps}>{childNode}</td>;
  };

export class Setup extends Component {
    constructor(props) {
        super(props)
    
        this.state = {
            primarydata: [],
            endpointsdata: [],
            selectedendpoint: '',
            dataSource: '',
        }
    }


    componentDidMount() {
        axios.get(baseUrl + 'api/v1/tables/runner')
            .then(response => {
                console.log(response.data)
                this.setState({
                    primarydata : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        axios.get(baseUrl + 'api/v1/tables/endpoints')
            .then(response => {
                this.setState({
                    endpointsdata : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        }

    ChangeData = (data) => {
        axios.post(baseUrl + 'tables/runner',{ crossdomain: true }, data)
            .then(response => {
                console.log(response)
            })
            .catch(function(error) {
                console.log(error);
            })
    }
    
    ref: any = null;

    rowClick = (e: any, row: any) => {
            console.log('ref table: ', this.ref.table); // this is the Tabulator table instance
            this.setState({ selectedendpoint: row.getData().endpoint });
          };

    handleSave = (row) => {
        this.ChangeData(row)
        const newData = [...this.state.primarydata];
        const index = newData.findIndex((item) => row.key === item.key);
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        this.setState({
            primarydata: newData,
        });
    };


    render() {
        const IconFormatter = (e) => {
            const rowData = e.cell._cell.row.data;
            return(
                <div>
                {rowData.host_type === 'MAC' ?
                (
                    <FontAwesomeIcon
                    icon={faApple}
                    size='2x'
                    />
                ) :
                ((rowData.host_type === 'UBUNTU' ?
                (
                    <FontAwesomeIcon
                    icon={faUbuntu}
                    size='2x'
                    />
                ) :
                (
                    <div>
                    <FontAwesomeIcon
                    icon={faWindows}
                    size='2x'
                    />
                    </div>
                )))
                }
                
                </div>
                )
        }
        const endpointcolumns = [
            { title: "Endpoint", field: "endpoint", headerFilter:true},
            { title: "Hostname", field: "hostname"},
            { title: "Host Type", field: "host_type", formatter: reactFormatter(<IconFormatter />)},
            { title: "Mgmt Ifname", field: "mgmt_ifname"},
            { title: "Mgmt Mac", field: "mgmt_mac"}
        ];
        const options = {
            movableRows: true,
            paginationSize:10,
            responsiveLayout:"hide",
            pagination:"local",
            movableColumns: true
          };

        const primaryColumns = [
            { title: "Key", key: "key", dataIndex: "key"},
            { title: "Value", key: "value", dataIndex: "value", editable: true,
              render: (value, record) => (
                  record.key === "IP" ?
                  <div>
                    <span>
                    {value} &nbsp; &nbsp; &nbsp;  <FontAwesomeIcon icon={faPencilAlt}/>
                  </span>
                  </div>
                   :
                   <div>
                  <span>
                    {value}
                  </span>
                  </div>
              )},
        ];

          const editablecolumns = primaryColumns.map((col) => {
            if (!col.editable) {
              return col;
            }

            return {
              ...col,
              onCell: (record) => ({
                record,
                editable: col.editable,
                dataIndex: col.dataIndex,
                title: col.title,
                handleSave: this.handleSave,
              }),
            };
          });

          const components = {
            body: {
                row: EditableRow,
                cell: EditableCell,
            },
          };


        return (

            <div>
            <Row style={{paddingBottom: 30}}>
            <Col style={{marginLeft: '220px'}} md={{ span: 10, offset:  1}}>
                <div>
                <h1 style={{textAlign:'center', fontSize: 22, fontWeight: 'bold', marginBottom: '20px'}}>Primary Node Info</h1>
                <Table
                    components={components}
                    columns={editablecolumns}
                    dataSource={this.state.primarydata}
                    bordered
                    rowClassName={() => 'editable-row'}
                    pagination={false}
                />
                </div>
                </Col>

            </Row>
            <Row>
            <label style={{marginLeft: '350px', fontSize: 22, fontWeight: 'bold', marginBottom: '20px'}}>Endpoints Data</label>
            <ReactTabulator
                    ref={(ref) => (this.ref = ref)}
                    rowClick={this.rowClick}    
                    data={this.state.endpointsdata}
                    columns={endpointcolumns}
                    tooltips={true}
                    options={options}
                    data-custom-attr="test-custom-attribute"
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    className="table-active table-light thead-dark table-striped table-primary table-bordered"          
                    />
            </Row>
            <div>
            {this.state.selectedendpoint ? (
                            <Redirect to={{
                                pathname:'/Endpoint',
                                state: { endpoint: this.state.selectedendpoint }
                            }}/>
                
            ) : (
                <div>
                </div>
            )}
            </div>
            </div>
        )
    }
}

export default Setup
